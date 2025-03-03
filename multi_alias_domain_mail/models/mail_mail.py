import ast
import base64
import psycopg2
import smtplib
import re

from collections import defaultdict
from odoo import api, models, tools, _
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

import logging

_logger = logging.getLogger(__name__)

from odoo.addons.mail.models.mail_mail import MailMail


def _split_by_mail_configuration(cls):
    """Group the <mail.mail> based on their "email_from", their "alias domain"
    and their "mail_server_id".

    The <mail.mail> will have the "same sending configuration" if they have the same
    mail server, alias domain and mail from. For performance purpose, we can use an SMTP
    session in batch and therefore we need to group them by the parameter that will
    influence the mail server used.

    The same "sending configuration" may repeat in order to limit batch size
    according to the `mail.session.batch.size` system parameter.

    Return iterators over
        mail_server_id, email_from, Records<mail.mail>.ids
    """
    mail_values = cls.read(['id', 'email_from', 'mail_server_id', 'record_alias_domain_id'])

    # First group the <mail.mail> per mail_server_id, per alias_domain (if no server) and per email_from
    group_per_email_from = defaultdict(list)
    for values in mail_values:
        mail_server_id = values['mail_server_id'][0] if values['mail_server_id'] else False
        alias_domain_id = values['record_alias_domain_id'][0] if values['record_alias_domain_id'] else False
        key = (mail_server_id, alias_domain_id, values['email_from'])
        group_per_email_from[key].append(values['id'])

    # Then find the mail server for each email_from and group the <mail.mail>
    # per mail_server_id and smtp_from
    mail_servers = cls.env['ir.mail_server'].sudo().search([], order='sequence, id')
    group_per_smtp_from = defaultdict(list)
    for (mail_server_id, alias_domain_id, email_from), mail_ids in group_per_email_from.items():
        if not mail_server_id:
            mail_server = cls.env['ir.mail_server']
            if alias_domain_id:
                alias_domain = cls.env['mail.alias.domain'].sudo().browse(alias_domain_id)
                mail_server = mail_server.with_context(
                    domain_notifications_email=alias_domain.default_from_email,
                    domain_bounce_address=alias_domain.bounce_email,
                )
            mail_server, smtp_from = mail_server._find_mail_server(email_from, mail_servers)
            mail_server_id = mail_server.id if mail_server else False
        else:
            smtp_from = email_from

        group_per_smtp_from[(mail_server_id, alias_domain_id, smtp_from)].extend(mail_ids)

    batch_size = int(cls.env['ir.config_parameter'].sudo().get_param('mail.session.batch.size')) or 1000
    for (mail_server_id, alias_domain_id, smtp_from), record_ids in group_per_smtp_from.items():
        for batch_ids in tools.split_every(batch_size, record_ids):
            yield mail_server_id, alias_domain_id, smtp_from, batch_ids

def send(cls, auto_commit=False, raise_exception=False):
    """ Sends the selected emails immediately, ignoring their current
        state (mails that have already been sent should not be passed
        unless they should actually be re-sent).
        Emails successfully delivered are marked as 'sent', and those
        that fail to be deliver are marked as 'exception', and the
        corresponding error mail is output in the server logs.

        :param bool auto_commit: whether to force a commit of the mail status
            after sending each mail (meant only for scheduler processing);
            should never be True during normal transactions (default: False)
        :param bool raise_exception: whether to raise an exception if the
            email sending process has failed
        :return: True
    """
    for mail_server_id, alias_domain_id, smtp_from, batch_ids in cls._split_by_mail_configuration():
        smtp_session = None
        try:
            smtp_session = cls.env['ir.mail_server'].connect(mail_server_id=mail_server_id, smtp_from=smtp_from)
        except Exception as exc:
            if raise_exception:
                # To be consistent and backward compatible with mail_mail.send() raised
                # exceptions, it is encapsulated into an Odoo MailDeliveryException
                raise MailDeliveryException(_('Unable to connect to SMTP Server'), exc)
            else:
                batch = cls.browse(batch_ids)
                batch.write({'state': 'exception', 'failure_reason': exc})
                batch._postprocess_sent_message(success_pids=[], failure_type="mail_smtp")
        else:
            cls.browse(batch_ids).with_context(alias_domain_id=alias_domain_id)._send(
                auto_commit=auto_commit,
                raise_exception=raise_exception,
                smtp_session=smtp_session
            )
            _logger.info(
                'Sent batch %s emails via mail server ID #%s',
                len(batch_ids), mail_server_id)
        finally:
            if smtp_session:
                smtp_session.quit()

def _send(cls, auto_commit=False, raise_exception=False, smtp_session=None):
    IrMailServer = cls.env['ir.mail_server']
    IrAttachment = cls.env['ir.attachment']
    alias_domain_id = cls._context.get("alias_domain_id", False)
    alias_domain = cls.env['mail.alias.domain'].sudo().browse(alias_domain_id) if alias_domain_id else False
    for mail_id in cls.ids:
        success_pids = []
        failure_type = None
        processing_pid = None
        mail = None
        try:
            mail = cls.browse(mail_id)
            if mail.state != 'outgoing':
                continue

            # remove attachments if user send the link with the access_token
            body = mail.body_html or ''
            attachments = mail.attachment_ids
            for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
                attachments = attachments - IrAttachment.browse(int(link))

            # load attachment binary data with a separate read(), as prefetching all
            # `datas` (binary field) could bloat the browse cache, triggerring
            # soft/hard mem limits with temporary data.
            attachments = [(a['name'], base64.b64decode(a['datas']), a['mimetype'])
                           for a in attachments.sudo().read(['name', 'datas', 'mimetype']) if a['datas'] is not False]

            # specific behavior to customize the send email for notified partners
            email_list = []
            if mail.email_to:
                email_list.append(mail._send_prepare_values())
            for partner in mail.recipient_ids:
                values = mail._send_prepare_values(partner=partner)
                values['partner_id'] = partner
                email_list.append(values)

            # headers
            headers = {'X-Odoo-Message-Id': mail.message_id}
            headers['Return-Path'] = alias_domain and alias_domain.bounce_email or cls.env.company.bounce_email
            if mail.headers:
                try:
                    headers.update(ast.literal_eval(mail.headers))
                except Exception:
                    pass

            # Writing on the mail object may fail (e.g. lock on user) which
            # would trigger a rollback *after* actually sending the email.
            # To avoid sending twice the same email, provoke the failure earlier
            mail.write({
                'state': 'exception',
                'failure_reason': _('Error without exception. Probably due to sending an email without computed recipients.'),
            })
            # Update notification in a transient exception state to avoid concurrent
            # update in case an email bounces while sending all emails related to current
            # mail record.
            notifs = cls.env['mail.notification'].search([
                ('notification_type', '=', 'email'),
                ('mail_mail_id', 'in', mail.ids),
                ('notification_status', 'not in', ('sent', 'canceled'))
            ])
            if notifs:
                notif_msg = _('Error without exception. Probably due to concurrent access update of notification records. Please see with an administrator.')
                notifs.sudo().write({
                    'notification_status': 'exception',
                    'failure_type': 'unknown',
                    'failure_reason': notif_msg,
                })
                # `test_mail_bounce_during_send`, force immediate update to obtain the lock.
                # see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
                notifs.flush_recordset(['notification_status', 'failure_type', 'failure_reason'])

            # protect against ill-formatted email_from when formataddr was used on an already formatted email
            emails_from = tools.email_split_and_format_normalize(mail.email_from)
            email_from = emails_from[0] if emails_from else mail.email_from

            # build an RFC2822 email.message.Message object and send it without queuing
            res = None
            # TDE note: could be great to pre-detect missing to/cc and skip sending it
            # to go directly to failed state update
            for email in email_list:

                if alias_domain_id:
                    alias_domain = cls.env['mail.alias.domain'].sudo().browse(alias_domain_id)
                    SendIrMailServer = IrMailServer.with_context(
                        domain_notifications_email=alias_domain.default_from_email,
                        domain_bounce_address=(email.get('headers') and email.get('headers').get('Return-Path')) or alias_domain.bounce_email,
                    )
                else:
                    SendIrMailServer = IrMailServer
                # give indication to 'send_mail' about emails already considered
                # as being valid
                email_to_normalized = email.pop('email_to_normalized', [])
                # support headers specific to the specific outgoing email
                if email.get('headers'):
                    email_headers = headers.copy()
                    try:
                        email_headers.update(email.get('headers'))
                    except Exception:  # noqa: BLE001
                        pass
                else:
                    email_headers = headers

                msg = SendIrMailServer.build_email(
                    email_from=email_from,
                    email_to=email.get('email_to'),
                    subject=mail.subject,
                    body=email.get('body'),
                    body_alternative=email.get('body_alternative'),
                    email_cc=tools.email_split_and_format_normalize(mail.email_cc),
                    reply_to=mail.reply_to,
                    attachments=attachments,
                    message_id=mail.message_id,
                    references=mail.references,
                    object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
                    subtype='html',
                    subtype_alternative='plain',
                    headers=email_headers)
                processing_pid = email.pop("partner_id", None)
                try:
                    # 'send_validated_to' restricts emails found by 'extract_rfc2822_addresses'
                    res = SendIrMailServer.with_context(send_validated_to=email_to_normalized).send_email(
                        msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
                    if processing_pid:
                        success_pids.append(processing_pid)
                    processing_pid = None
                except AssertionError as error:
                    if str(error) == IrMailServer.NO_VALID_RECIPIENT:
                        # if we have a list of void emails for email_list -> email missing, otherwise generic email failure
                        if not email.get('email_to') and failure_type != "mail_email_invalid":
                            failure_type = "mail_email_missing"
                        else:
                            failure_type = "mail_email_invalid"
                        # No valid recipient found for this particular
                        # mail item -> ignore error to avoid blocking
                        # delivery to next recipients, if any. If this is
                        # the only recipient, the mail will show as failed.
                        _logger.info("Ignoring invalid recipients for mail.mail %s: %s",
                                     mail.message_id, email.get('email_to'))
                    else:
                        raise
            if res:  # mail has been sent at least once, no major exception occurred
                mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
                _logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
                # /!\ can't use mail.state here, as mail.refresh() will cause an error
                # see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
            mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
        except MemoryError:
            # prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
            # instead of marking the mail as failed
            _logger.exception(
                'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
                mail.id, mail.message_id)
            # mail status will stay on ongoing since transaction will be rollback
            raise
        except (psycopg2.Error, smtplib.SMTPServerDisconnected):
            # If an error with the database or SMTP session occurs, chances are that the cursor
            # or SMTP session are unusable, causing further errors when trying to save the state.
            _logger.exception(
                'Exception while processing mail with ID %r and Msg-Id %r.',
                mail.id, mail.message_id)
            raise
        except Exception as e:
            failure_reason = tools.ustr(e)
            _logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
            mail.write({'state': 'exception', 'failure_reason': failure_reason})
            mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason, failure_type='unknown')
            if raise_exception:
                if isinstance(e, (AssertionError, UnicodeEncodeError)):
                    if isinstance(e, UnicodeEncodeError):
                        value = "Invalid text: %s" % e.object
                    else:
                        value = '. '.join(e.args)
                    raise MailDeliveryException(value)
                raise

        if auto_commit is True:
            cls._cr.commit()
    return True

MailMail._send = _send
MailMail.send = send
MailMail._split_by_mail_configuration = _split_by_mail_configuration

