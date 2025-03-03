import ast
import base64
import psycopg2
import smtplib
import re
from markupsafe import Markup, escape
from collections import defaultdict
from email.message import EmailMessage
from odoo import api, models, tools, _
from odoo.addons.mail.models.mail_thread import MailThread as BaseMailThread
from odoo.tools import is_html_empty

import logging

_logger = logging.getLogger(__name__)


@api.model
def get_empty_list_help(self, help):
    """ Override of BaseModel.get_empty_list_help() to generate an help message
    that adds alias information. """
    model = self._context.get('empty_list_help_model')
    res_id = self._context.get('empty_list_help_id')
    document_name = self._context.get('empty_list_help_document_name', _('document'))
    nothing_here = is_html_empty(help)
    alias = None

    # specific res_id -> find its alias (i.e. section_id specified)
    if model and res_id:
        record = self.env[model].sudo().browse(res_id)
        # check that the alias effectively creates new records
        if ('alias_id' in record and record.alias_id and
            record.alias_id.alias_name and record.alias_id.alias_domain and
            record.alias_id.alias_model_id.model == self._name and
            record.alias_id.alias_force_thread_id == 0):
            alias = record.alias_id
    # no res_id or res_id not linked to an alias -> generic help message, take a generic alias of the model
    if not alias and model and self.env.company.alias_domain_id:
        aliases = self.env['mail.alias'].search([
            ("alias_domain_id", "=", self.env.company.alias_domain_id.id),
            ("alias_parent_model_id.model", "=", model),
            ("alias_name", "!=", False),
            ('alias_force_thread_id', '=', False),
            ('alias_parent_thread_id', '=', False)], order='id ASC')
        if aliases and len(aliases) == 1:
            alias = aliases[0]

    if alias:
        email_link = "<a href='mailto:%(email)s'>%(email)s</a>" % {'email': alias.display_name}
        if nothing_here:
            return "<p class='o_view_nocontent_smiling_face'>%(dyn_help)s</p>" % {
                'dyn_help': _("Add a new %(document)s or send an email to %(email_link)s",
                              document=document_name,
                              email_link=email_link,
                              )
            }
        # do not add alias two times if it was added previously
        if "oe_view_nocontent_alias" not in help:
            return "%(static_help)s<p class='oe_view_nocontent_alias'>%(dyn_help)s</p>" % {
                'static_help': help,
                'dyn_help': _("Create new %(document)s by sending an email to %(email_link)s",
                              document=document_name,
                              email_link=email_link,
                              )
            }

    if nothing_here:
        return "<p class='o_view_nocontent_smiling_face'>%(dyn_help)s</p>" % {
            'dyn_help': _("Create new %(document)s", document=document_name),
        }

    return help

def _routing_create_bounce_email(self, email_from, body_html, message, **mail_values):
    bounce_to = tools.decode_message_header(message, 'Return-Path') or email_from
    bounce_mail_values = {
        'author_id': False,
        'body_html': body_html,
        'subject': 'Re: %s' % message.get('subject'),
        'email_to': bounce_to,
        'auto_delete': True,
    }
    email_from = False
    if bounce_from := self.env.company.bounce_email:
        email_from = tools.formataddr(('MAILER-DAEMON', bounce_from))
    if not email_from:
        catchall_aliases = self.env['mail.alias.domain'].search([]).mapped('catchall_email')
        if not any(catchall_email in message['To'] for catchall_email in catchall_aliases):
            email_from = tools.decode_message_header(message, 'To')
    if not email_from:
        email_from = tools.formataddr(('MAILER-DAEMON', self.env.user.email_normalized))

    bounce_mail_values['email_from'] = email_from
    bounce_mail_values.update(mail_values)
    self.env['mail.mail'].sudo().create(bounce_mail_values).send()


def _mail_find_user_for_gateway(self, email_value, alias=None):
    """ Utility method to find user from email address that can create documents
    in the target model. Purpose is to link document creation to users whenever
    possible, for example when creating document through mailgateway.

    Heuristic

      * alias owner record: fetch in its followers for user with matching email;
      * find any user with matching emails;
      * try alias owner as fallback;

    Note that standard search order is applied.

    :param str email_value: will be sanitized and parsed to find email;
    :param mail.alias alias: optional alias. Used to fetch owner followers
      or fallback user (alias owner);

    :return res.user user: user matching email or void recordset if none found
    """
    # find normalized emails and exclude aliases (to avoid subscribing alias emails to records)
    normalized_email = tools.email_normalize(email_value)
    if not normalized_email:
        return self.env['res.users']

    if self.env['mail.alias'].sudo().search_count([('alias_full_name', '=', email_value)]):
        return self.env['res.users']

    if alias and alias.alias_parent_model_id and alias.alias_parent_thread_id:
        followers = self.env['mail.followers'].search([
            ('res_model', '=', alias.alias_parent_model_id.sudo().model),
            ('res_id', '=', alias.alias_parent_thread_id)]
        ).mapped('partner_id')
    else:
        followers = self.env['res.partner']

    follower_users = self.env['res.users'].search([
        ('partner_id', 'in', followers.ids), ('email_normalized', '=', normalized_email)
    ], limit=1) if followers else self.env['res.users']
    matching_user = follower_users[0] if follower_users else self.env['res.users']
    if matching_user:
        return matching_user

    if not matching_user:
        std_users = self.env['res.users'].sudo().search([('email_normalized', '=', normalized_email)], limit=1)
        matching_user = std_users[0] if std_users else self.env['res.users']

    if not matching_user and alias and alias.alias_user_id:
        matching_user = alias and alias.alias_user_id
    if matching_user:
        return matching_user

    return matching_user

@api.model
def _mail_find_partner_from_emails(self, emails, records=None, force_create=False, extra_domain=False):
    """ Utility method to find partners from email addresses. If no partner is
    found, create new partners if force_create is enabled. Search heuristics

      * 0: clean incoming email list to use only normalized emails. Exclude
           those used in aliases to avoid setting partner emails to emails
           used as aliases;
      * 1: check in records (record set) followers if records is mail.thread
           enabled and if check_followers parameter is enabled;
      * 2: search for partners with user;
      * 3: search for partners;

    :param records: record set on which to check followers;
    :param list emails: list of email addresses for finding partner;
    :param boolean force_create: create a new partner if not found

    :return list partners: a list of partner records ordered as given emails.
      If no partner has been found and/or created for a given emails its
      matching partner is an empty record.
    """
    if records and isinstance(records, self.pool['mail.thread']):
        followers = records.mapped('message_partner_ids')
    else:
        followers = self.env['res.partner']

    # first, build a normalized email list and remove those linked to aliases
    # to avoid adding aliases as partners. In case of multi-email input, use
    # the first found valid one to be tolerant against multi emails encoding
    normalized_emails = [email_normalized
                         for email_normalized in (tools.email_normalize(contact, strict=False) for contact in emails)
                         if email_normalized
                         ]
    matching_aliases = self.env['mail.alias'].sudo().search([('alias_full_name', 'in', normalized_emails)])
    if matching_aliases:
        normalized_emails = [email for email in normalized_emails if
                             email not in matching_aliases.mapped('alias_full_name')]

    done_partners = [follower for follower in followers if follower.email_normalized in normalized_emails]
    remaining = [email for email in normalized_emails if email not in [partner.email_normalized for partner in done_partners]]

    user_partners = self._mail_search_on_user(remaining, extra_domain=extra_domain)
    done_partners += [user_partner for user_partner in user_partners]
    remaining = [email for email in normalized_emails if email not in [partner.email_normalized for partner in done_partners]]

    partners = self._mail_search_on_partner(remaining, extra_domain=extra_domain)
    done_partners += [partner for partner in partners]
    # prioritize current user if exists in list, and partners with matching company ids
    if company_fname := records and records._mail_get_company_field():
        def sort_key(p):
            return (
                self.env.user.partner_id == p,  # prioritize user
                p.company_id in records[company_fname],  # then partner associated w/ records
                not p.company_id,  # else pick partner w/out company_id
            )
    else:
        def sort_key(p):
            return (self.env.user.partner_id == p, not p.company_id)
    # prioritize current user if exists in list, and partners with matching company ids
    done_partners.sort(key=sort_key, reverse=True) # reverse because False < True

    # iterate and keep ordering
    partners = []
    for contact in emails:
        normalized_email = tools.email_normalize(contact, strict=False)
        partner = next((partner for partner in done_partners if partner.email_normalized == normalized_email), self.env['res.partner'])
        if not partner and force_create and normalized_email in normalized_emails:
            partner = self.env['res.partner'].browse(self.env['res.partner'].name_create(contact)[0])
        partners.append(partner)
    return partners

@api.returns('mail.message', lambda value: value.id)
def message_post(self, *,
                 body='', subject=None, message_type='notification',
                 email_from=None, author_id=None, parent_id=False,
                 subtype_xmlid=None, subtype_id=False, partner_ids=None,
                 attachments=None, attachment_ids=None,
                 **kwargs):
    """ Post a new message in an existing thread, returning the new mail.message.

    :param str body: body of the message, usually raw HTML that will
        be sanitized
    :param str subject: subject of the message
    :param str message_type: see mail_message.message_type field. Can be anything but
        user_notification, reserved for message_notify
    :param str email_from: from address of the author. See ``_message_compute_author``
        that uses it to make email_from / author_id coherent;
    :param int author_id: optional ID of partner record being the author. See
        ``_message_compute_author`` that uses it to make email_from / author_id coherent;
    :param int parent_id: handle thread formation
    :param int subtype_id: subtype_id of the message, used mainly for followers
        notification mechanism;
    :param list(int) partner_ids: partner_ids to notify in addition to partners
        computed based on subtype / followers matching;
    :param list(tuple(str,str), tuple(str,str, dict)) attachments : list of attachment
        tuples in the form ``(name,content)`` or ``(name,content, info)`` where content
        is NOT base64 encoded;
    :param list attachment_ids: list of existing attachments to link to this message
        -Should only be set by chatter
        -Attachment object attached to mail.compose.message(0) will be attached
            to the related document.

    Extra keyword arguments will be used either
      * as default column values for the new mail.message record if they match
        mail.message fields;
      * propagated to notification methods;

    :return record: newly create mail.message
    """
    self.ensure_one()  # should always be posted on a record, use message_notify if no record
    # split message additional values from notify additional values
    msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
    notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)

    # preliminary value safety check
    partner_ids = set(partner_ids or [])
    if self._name == 'mail.thread' or not self.id or message_type == 'user_notification':
        raise ValueError(_('Posting a message should be done on a business document. Use message_notify to send a notification to an user.'))
    if 'channel_ids' in kwargs:
        raise ValueError(_("Posting a message with channels as listeners is not supported since Odoo 14.3+. Please update code accordingly."))
    if 'model' in msg_kwargs or 'res_id' in msg_kwargs:
        raise ValueError(_("message_post does not support model and res_id parameters anymore. Please call message_post on record."))
    if 'subtype' in kwargs:
        raise ValueError(_("message_post does not support subtype parameter anymore. Please give a valid subtype_id or subtype_xmlid value instead."))
    if any(not isinstance(pc_id, int) for pc_id in partner_ids):
        raise ValueError(_('message_post partner_ids and must be integer list, not commands.'))

    self = self._fallback_lang() # add lang to context immediately since it will be useful in various flows latter.

    # Find the message's author
    guest = self.env['mail.guest']._get_guest_from_context()
    if self.env.user._is_public() and guest:
        author_guest_id = guest.id
        author_id, email_from = False, False
    else:
        author_guest_id = False
        author_id, email_from = self._message_compute_author(author_id, email_from, raise_on_email=True)

    if subtype_xmlid:
        subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
    if not subtype_id:
        subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

    # automatically subscribe recipients if asked to
    if self._context.get('mail_post_autofollow') and partner_ids:
        self.message_subscribe(partner_ids=list(partner_ids))

    msg_values = dict(msg_kwargs)
    if 'email_add_signature' not in msg_values:
        msg_values['email_add_signature'] = True
    if not msg_values.get('record_name'):
        # use sudo as record access is not always granted (notably when replying
        # a notification) -> final check is done at message creation level
        msg_values['record_name'] = self.sudo().display_name
    if 'record_alias_domain_id' not in msg_values:
        msg_values['record_alias_domain_id'] = self.sudo()._mail_get_alias_domains(default_company=self.env.company)[
            self.id].id
    msg_values.update({
        'author_id': author_id,
        'author_guest_id': author_guest_id,
        'email_from': email_from,
        'model': self._name,
        'res_id': self.id,
        # content
        'body': body,
        'subject': subject or False,
        'message_type': message_type,
        'parent_id': self._message_compute_parent_id(parent_id),
        'subtype_id': subtype_id,
        # recipients
        'partner_ids': partner_ids,
    })

    attachments = attachments or []
    attachment_ids = attachment_ids or []
    attachement_values = self._message_post_process_attachments(attachments, attachment_ids, msg_values)
    msg_values.update(attachement_values)  # attachement_ids, [body]

    new_message = self._message_create(msg_values)

    # Set main attachment field if necessary. Call as sudo as people may post
    # without read access on the document, notably when replying on a
    # notification, which makes attachments check crash.
    self.sudo()._message_set_main_attachment_id(msg_values['attachment_ids'])

    if msg_values['author_id'] and msg_values['message_type'] != 'notification' and not self._context.get('mail_create_nosubscribe'):
        if self.env['res.partner'].browse(msg_values['author_id']).active:  # we dont want to add odoobot/inactive as a follower
            self._message_subscribe(partner_ids=[msg_values['author_id']])

    self._message_post_after_hook(new_message, msg_values)
    self._notify_thread(new_message, msg_values, **notif_kwargs)
    return new_message

def message_notify(self, *,
                   partner_ids=False, parent_id=False, model=False, res_id=False,
                   author_id=None, email_from=None, body='', subject=False, **kwargs):
    """ Shortcut allowing to notify partners of messages that shouldn't be
    displayed on a document. It pushes notifications on inbox or by email depending
    on the user configuration, like other notifications. """
    if self:
        self.ensure_one()
    # split message additional values from notify additional values
    msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
    notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)

    author_id, email_from = self._message_compute_author(author_id, email_from, raise_on_email=True)

    if not partner_ids:
        _logger.warning('Message notify called without recipient_ids, skipping')
        return self.env['mail.message']

    # allow to link a notification to a document that does not inherit from
    # MailThread by supporting model / res_id
    if not (model and res_id):  # both value should be set or none should be set (record)
        model = False
        res_id = False

    msg_values = {
        'parent_id': parent_id,
        'model': self._name if self else model,
        'res_id': self.id if self else res_id,
        'message_type': 'user_notification',
        'subject': subject,
        'body': body,
        'author_id': author_id,
        'email_from': email_from,
        'partner_ids': partner_ids,
        'is_internal': True,
        'record_name': False,
        'message_id': tools.generate_tracking_message_id('message-notify'),
    }
    msg_values.update(msg_kwargs)
    # add default-like values afterwards, to avoid useless queries
    if 'subtype_id' not in msg_values:
        msg_values['subtype_id'] = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
    if 'reply_to' not in msg_values:
        msg_values['reply_to'] = self._notify_get_reply_to(default=email_from)[self.id if self else False]
    if 'email_add_signature' not in msg_values:
        msg_values['email_add_signature'] = True
    if self:
        if 'record_alias_domain_id' not in msg_values:
            msg_values['record_alias_domain_id'] = self._mail_get_alias_domains(default_company=self.env.company)[
                self.id].id
    new_message = self._message_create(msg_values)
    self._notify_thread(new_message, msg_values, **notif_kwargs)
    return new_message

def _message_log_batch(self, bodies, author_id=None, email_from=None, subject=False, message_type='notification'):
    """ Shortcut allowing to post notes on a batch of documents. It achieve the
    same purpose as _message_log, done in batch to speedup quick note log.

      :param bodies: dict {record_id: body}
    """
    author_id, email_from = self._message_compute_author(author_id, email_from, raise_on_email=False)

    base_message_values = {
        'subject': subject,
        'author_id': author_id,
        'email_from': email_from,
        'message_type': message_type,
        'model': self._name,
        'record_alias_domain_id': False,
        'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
        'is_internal': True,
        'record_name': False,
        'reply_to': self.env['mail.thread']._notify_get_reply_to(default=email_from)[False],
        'message_id': tools.generate_tracking_message_id('message-notify'),  # why? this is all but a notify
        'email_add_signature': False,
    }
    values_list = [dict(base_message_values,
                        res_id=record.id,
                        body=bodies.get(record.id, ''))
                   for record in self]
    return self.sudo()._message_create(values_list)

@api.model
def message_route(self, message, message_dict, model=None, thread_id=None, custom_values=None):
    """ Attempt to figure out the correct target model, thread_id,
    custom_values and user_id to use for an incoming message.
    Multiple values may be returned, if a message had multiple
    recipients matching existing mail.aliases, for example.

    The following heuristics are used, in this order:

     * if the message replies to an existing thread by having a Message-Id
       that matches an existing mail_message.message_id, we take the original
       message model/thread_id pair and ignore custom_value as no creation will
       take place;
     * look for a mail.alias entry matching the message recipients and use the
       corresponding model, thread_id, custom_values and user_id. This could
       lead to a thread update or creation depending on the alias;
     * fallback on provided ``model``, ``thread_id`` and ``custom_values``;
     * raise an exception as no route has been found

    :param string message: an email.message instance
    :param dict message_dict: dictionary holding parsed message variables
    :param string model: the fallback model to use if the message does not match
        any of the currently configured mail aliases (may be None if a matching
        alias is supposed to be present)
    :type dict custom_values: optional dictionary of default field values
        to pass to ``message_new`` if a new record needs to be created.
        Ignored if the thread record already exists, and also if a matching
        mail.alias was found (aliases define their own defaults)
    :param int thread_id: optional ID of the record/thread from ``model`` to
        which this mail should be attached. Only used if the message does not
        reply to an existing thread and does not match any mail alias.
    :return: list of routes [(model, thread_id, custom_values, user_id, alias)]

    :raises: ValueError, TypeError
    """
    if not isinstance(message, EmailMessage):
        raise TypeError('message must be an email.message.EmailMessage at this point')
    catchall_domains_allowed = list(filter(None, (self.env["ir.config_parameter"].sudo().get_param(
        "mail.catchall.domain.allowed") or '').split(',')))
    if catchall_domains_allowed:
        catchall_domains_allowed += self.env['mail.alias.domain'].search([]).mapped('name')

    def _filter_excluded_local_part(email):
        left, _at, domain = email.partition('@')
        if not domain:
            return False
        if catchall_domains_allowed and domain not in catchall_domains_allowed:
            return False
        return left
    fallback_model = model
    # 0. Handle bounce: verify whether this is a bounced email and use it to collect bounce data and update notifications for customers
    #    Bounce alias: if any To contains bounce_alias@domain
    #    Bounce message (not alias)
    #       See http://datatracker.ietf.org/doc/rfc3462/?include_text=1
    #        As all MTA does not respect this RFC (googlemail is one of them),
    #       we also need to verify if the message come from "mailer-daemon"
    #    If not a bounce: reset bounce information
    bounce_aliases = self.env['mail.alias.domain'].search([]).mapped('bounce_email')
    email_to_list = [
        tools.email_normalize(e) or e
        for e in (tools.email_split(message_dict['to']) or [''])
    ]
    if bounce_aliases and any(email in bounce_aliases for email in email_to_list):
        self._routing_handle_bounce(message, message_dict)
        return []
    email_from = message_dict['email_from']
    email_from_localpart = (tools.email_split(email_from) or [''])[0].split('@', 1)[0].lower()

    # detection based on email_from
    if email_from_localpart == 'mailer-daemon':
        self._routing_handle_bounce(message, message_dict)
        return []

    # detection based on content type
    content_type = message.get_content_type()
    if content_type == 'multipart/report' or 'report-type=delivery-status' in content_type:
        self._routing_handle_bounce(message, message_dict)
        return []
    self._routing_reset_bounce(message, message_dict)
    # get email.message.Message variables for future processing
    message_id = message_dict['message_id']

    # compute references to find if message is a reply to an existing thread
    thread_references = message_dict['references'] or message_dict['in_reply_to']
    msg_references = [r.strip() for r in tools.unfold_references(thread_references) if 'reply_to' not in r]
    mail_messages = self.env['mail.message'].sudo().search([('message_id', 'in', msg_references)], limit=1, order='id desc, message_id')
    is_a_reply = bool(mail_messages)
    reply_model, reply_thread_id = mail_messages.model, mail_messages.res_id

    # author and recipients
    email_to_list = [e.lower() for e in (tools.email_split(message_dict['to']) or [''])]
    email_to_localparts = list(filter(None, (_filter_excluded_local_part(email_to) for email_to in email_to_list)))
    # Delivered-To is a safe bet in most modern MTAs, but we have to fallback on To + Cc values
    # for all the odd MTAs out there, as there is no standard header for the envelope's `rcpt_to` value.
    rcpt_tos_list = [e.lower() for e in (tools.email_split(message_dict['recipients']) or [''])]
    rcpt_tos_localparts = list(filter(None, (_filter_excluded_local_part(email_to) for email_to in rcpt_tos_list)))
    rcpt_tos_valid_list = list(rcpt_tos_list)



    # 1. Handle reply
    #    if destination = alias with different model -> consider it is a forward and not a reply
    #    if destination = alias with same model -> check contact settings as they still apply
    if reply_model and reply_thread_id:
        reply_model_id = self.env['ir.model']._get_id(reply_model)
        other_model_aliases = self.env['mail.alias'].search([
            '&',
            ('alias_model_id', '!=', reply_model_id),
            '|',
            ('alias_full_name', 'in', email_to_list),
            '&', ('alias_name', 'in', email_to_localparts), ('alias_incoming_local', '=', True),
        ])
        if other_model_aliases:
            is_a_reply, reply_model, reply_thread_id = False, False, False
            rcpt_tos_valid_list = [
                to
                for to in rcpt_tos_valid_list
                if (
                        to in other_model_aliases.mapped('alias_full_name')
                        or to.split('@', 1)[0] in other_model_aliases.filtered('alias_incoming_local').mapped(
                    'alias_name')
                )
            ]
    rcpt_tos_valid_localparts = list(
        filter(None, (_filter_excluded_local_part(email_to) for email_to in rcpt_tos_valid_list)))

    if is_a_reply and reply_model:
        reply_model_id = self.env['ir.model']._get_id(reply_model)
        dest_aliases = self.env['mail.alias'].search([
            '&',
            ('alias_model_id', '=', reply_model_id),
            '|',
            ('alias_full_name', 'in', rcpt_tos_list),
            '&', ('alias_name', 'in', rcpt_tos_localparts), ('alias_incoming_local', '=', True),
        ], limit=1)

        user_id = self._mail_find_user_for_gateway(email_from, alias=dest_aliases).id or self._uid
        route = self._routing_check_route(
            message, message_dict,
            (reply_model, reply_thread_id, custom_values, user_id, dest_aliases),
            raise_exception=False)
        if route:
            _logger.info(
                'Routing mail from %s to %s with Message-Id %s: direct reply to msg: model: %s, thread_id: %s, custom_values: %s, uid: %s',
                email_from, message_dict['to'], message_id, reply_model, reply_thread_id, custom_values, self._uid)
            return [route]
        elif route is False:
            return []

    # 2. Handle new incoming email by checking aliases and applying their settings
    catchall_aliases = self.env['mail.alias.domain'].search([]).mapped('catchall_email')
    self = self.with_context(mail_catchall_aliases=catchall_aliases)
    if rcpt_tos_list:
        # no route found for a matching reference (or reply), so parent is invalid
        message_dict.pop('parent_id', None)
        # check it does not directly contact catchall
        if self._detect_write_to_catchall(message_dict):
            _logger.info('Routing mail from %s to %s with Message-Id %s: direct write to catchall, bounce', email_from, message_dict['to'], message_id)
            body = self.env['ir.qweb']._render('mail.mail_bounce_catchall', {
                'message': message,
            })
            self._routing_create_bounce_email(
                email_from, body, message,
                # add a reference with a tag, to be able to ignore response to this email
                references=f'{message_id} {tools.generate_tracking_message_id("loop-detection-bounce-email")}',
                reply_to=self.env.company.email)
            return []

        dest_aliases = self.env['mail.alias'].search([
            '|',
            ('alias_full_name', 'in', rcpt_tos_valid_list),
            '&', ('alias_name', 'in', rcpt_tos_valid_localparts), ('alias_incoming_local', '=', True),
        ])
        if dest_aliases:
            routes = []
            for alias in dest_aliases:
                user_id = self._mail_find_user_for_gateway(email_from, alias=alias).id or self._uid
                route = (alias.sudo().alias_model_id.model, alias.alias_force_thread_id, ast.literal_eval(alias.alias_defaults), user_id, alias)
                route = self._routing_check_route(message, message_dict, route, raise_exception=True)
                if route:
                    _logger.info(
                        'Routing mail from %s to %s with Message-Id %s: direct alias match: %r',
                        email_from, message_dict['to'], message_id, route)
                    routes.append(route)
            return routes

    # 3. Fallback to the provided parameters, if they work
    if fallback_model:
        # no route found for a matching reference (or reply), so parent is invalid
        message_dict.pop('parent_id', None)
        user_id = self._mail_find_user_for_gateway(email_from).id or self._uid
        route = self._routing_check_route(
            message, message_dict,
            (fallback_model, thread_id, custom_values, user_id, None),
            raise_exception=True)
        if route:
            _logger.info(
                'Routing mail from %s to %s with Message-Id %s: fallback to model:%s, thread_id:%s, custom_values:%s, uid:%s',
                email_from, message_dict['to'], message_id, fallback_model, thread_id, custom_values, user_id)
            return [route]

    # 4. Recipients contain catchall and unroutable emails -> bounce
    if rcpt_tos_list and self.with_context(mail_catchall_write_any_to=True)._detect_write_to_catchall(message_dict):
        _logger.info(
            'Routing mail from %s to %s with Message-Id %s: write to catchall + other unroutable emails, bounce',
            email_from, message_dict['to'], message_id
        )
        body = self.env['ir.qweb']._render('mail.mail_bounce_catchall', {
            'message': message,
        })
        self._routing_create_bounce_email(
            email_from, body, message,
            # add a reference with a tag, to be able to ignore response to this email
            references=f'{message_id} {tools.generate_tracking_message_id("loop-detection-bounce-email")}',
            reply_to=self.env.company.email)
        return []

    # ValueError if no routes found and if no bounce occurred
    raise ValueError(
        'No possible route found for incoming message from %s to %s (Message-Id %s:). '
        'Create an appropriate mail.alias or force the destination model.' %
        (email_from, message_dict['to'], message_id)
    )


BaseMailThread.get_empty_list_help = get_empty_list_help
BaseMailThread._routing_create_bounce_email = _routing_create_bounce_email
BaseMailThread._mail_find_user_for_gateway = _mail_find_user_for_gateway
BaseMailThread._mail_find_partner_from_emails = _mail_find_partner_from_emails
BaseMailThread.message_post = message_post
BaseMailThread.message_notify = message_notify
BaseMailThread.message_notify = message_notify

class MailThread(models.AbstractModel):
    _inherit = 'mail.alias'


    def _notify_by_email_get_base_mail_values(self, message, additional_values=None):
        base_mail_values = super()._notify_by_email_get_base_mail_values(message=message,additional_values=additional_values)
        if 'headers' in base_mail_values:
            message_sudo = message.sudo()
            if message_sudo.record_alias_domain_id.bounce_email:
                base_mail_values['headers']['Return-Path'] = message_sudo.record_alias_domain_id.bounce_email
        return base_mail_values

    @api.model
    def _detect_write_to_catchall(self, msg_dict):
        """Return True if directly contacts catchall."""
        # Note: tweaked in stable to avoid doing two times same search due to bugfix
        # (see odoo/odoo#161782), to clean when reaching master
        if self.env.context.get("mail_catchall_aliases"):
            catchall_aliases = self.env.context["mail_catchall_aliases"]
        else:
            catchall_aliases = self.env['mail.alias.domain'].search([]).mapped('catchall_email')

        email_to_list = [
            tools.email_normalize(e) or e
            for e in (tools.email_split(msg_dict['to']) or [''])
        ]
        # check it does not directly contact catchall; either (legacy) strict aka
        # all TOs belong are catchall, either (optional) any catchall in all TOs
        if self.env.context.get("mail_catchall_write_any_to"):
            return catchall_aliases and any(email_to in catchall_aliases for email_to in email_to_list)
        return (
            catchall_aliases and email_to_list and
            all(email_to in catchall_aliases for email_to in email_to_list)
        )