from collections import defaultdict
from odoo import api, models, tools, _

import logging

_logger = logging.getLogger(__name__)

from odoo.addons.mail.models.models import BaseModel


def _notify_get_reply_to(cls, default=None):
    """ Override to look for aliases based on alias domains
    """
    _records = cls
    model = _records._name if _records and _records._name != 'mail.thread' else False
    res_ids = _records.ids if _records and model else []
    _res_ids = res_ids or [False]  # always have a default value located in False

    result_email = dict()
    doc_names = dict()

    # group ids per company
    if res_ids:
        company_to_res_ids = defaultdict(list)
        record_ids_to_company = _records._mail_get_companies(default=cls.env.company)
        for record_id, company in record_ids_to_company.items():
            company_to_res_ids[company].append(record_id)
    else:
        company_to_res_ids = {cls.env.company: _res_ids}
        record_ids_to_company = {_res_id: cls.env.company for _res_id in _res_ids}


    if model and res_ids:
        if not doc_names:
            doc_names = dict((rec.id, rec.display_name) for rec in _records)
        mail_aliases = cls.env['mail.alias'].sudo().search([
            ('alias_domain_id', '!=', False),
            ('alias_parent_model_id.model', '=', model),
            ('alias_parent_thread_id', 'in', res_ids),
            ('alias_name', '!=', False)
        ])
        # take only first found alias for each thread_id, to match order (1 found -> limit=1 for each res_id)
        for alias in mail_aliases:
            result_email.setdefault(alias.alias_parent_thread_id, alias.alias_full_name)

    # left ids: use catchall
    left_ids = set(_res_ids) - set(result_email)
    if left_ids:
        for company, record_ids in company_to_res_ids.items():
            # left ids: use catchall defined on company alias domain
            if company.catchall_email:
                left_ids = set(record_ids) - set(result_email)
                if left_ids:
                    result_email.update({rec_id: company.catchall_email for rec_id in left_ids})

    reply_to_formatted = dict.fromkeys(_res_ids, default)
    for res_id, record_reply_to in result_email.items():
        reply_to_formatted[res_id] = cls._notify_get_reply_to_formatted_email(
            record_reply_to, doc_names.get(res_id) or '', company=record_ids_to_company[res_id],
        )
    return reply_to_formatted

def _notify_get_reply_to_formatted_email(cls, record_email, record_name, company=False):
    """
    :param <res.company> company: if given, setup the company used to
      complete name in formataddr. Otherwise fallback on 'company_id'
      of self or environment company;
    """
    length_limit = 68  # 78 - len('Reply-To: '), 78 per RFC
    # address itself is too long : return only email and log warning
    if len(record_email) >= length_limit:
        _logger.warning('Notification email address for reply-to is longer than 68 characters. '
            'This might create non-compliant folding in the email header in certain DKIM '
            'verification tech stacks. It is advised to shorten it if possible. '
            'Record name (if set): %s '
            'Reply-To: %s ', record_name, record_email)
        return record_email

    if not company:
        if len(cls) == 1:
            company = cls.sudo()._mail_get_companies(default=cls.env.company)
        else:
            company = cls.env.company

    # try company.name + record_name, or record_name alone (or company.name alone)
    name = f"{company.name} {record_name}" if record_name else company.name

    formatted_email = tools.formataddr((name, record_email))
    if len(formatted_email) > length_limit:
        formatted_email = tools.formataddr((record_name or company.name, record_email))
    if len(formatted_email) > length_limit:
        formatted_email = record_email
    return formatted_email


BaseModel._notify_get_reply_to = _notify_get_reply_to
BaseModel._notify_get_reply_to_formatted_email = _notify_get_reply_to_formatted_email


class Base(models.AbstractModel):
    _inherit = 'base'

    def _mail_get_alias_domains(self, default_company=False):
        """ Return alias domain linked to each record in self. It is based
        on the company (record's company, environment company) and fallback
        on the first found alias domain if configuration is not correct.

        :param <res.company> default_company: default company in case records
          have no company (or no company field); defaults to env.company;

        :return: for each record ID in self, found <mail.alias.domain>
        """
        record_companies = self._mail_get_companies(default=(default_company or self.env.company))

        # prepare default alias domain, fetch only if necessary
        default_domain = (default_company or self.env.company).alias_domain_id
        all_companies = self.env['res.company'].browse({comp.id for comp in record_companies.values()})
        # early optimization: search only if necessary
        if not default_domain and any(not comp.alias_domain_id for comp in all_companies):
            default_domain = self.env['mail.alias.domain'].search([], limit=1)

        return {
            record.id: (
                record_companies[record.id].alias_domain_id or default_domain
            )
            for record in self
        }

    @api.model
    def _mail_get_company_field(self):
        return 'company_id' if 'company_id' in self else False

    def _mail_get_companies(self, default=False):
        """ Return company linked to each record in self.

        :param <res.company> default: default value if no company field is found
          or if it holds a void value. Defaults to a void recordset;

        :return: for each record ID in self, found <res.company>
        """
        default_company = default or self.env['res.company']
        company_fname = self._mail_get_company_field()
        return {
            record.id: (record[company_fname] or default_company) if company_fname else default_company
            for record in self
        }
