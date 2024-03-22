# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"
    _order = "is_off_balance, sort_code, code, company_id"

    # FIXME: This should be English with Dutch translation
    referentiecode = fields.Char()
    sort_code = fields.Char(string="Sorting code")

    def write(self, vals):
        resp = super(AccountAccount, self).write(vals)

        for rec in self.filtered(
            lambda acc: not acc.referentiecode
            and acc.group_id
            and acc.group_id.referentiecode
        ):
            rec.referentiecode = rec.group_id.referentiecode
        if not self._context.get("group_allowed_journal_change"):
            self.group_set_allowed_journals()
        return resp

    def group_set_allowed_journals(self):
        for rec in self:
            if rec.group_id and rec.group_id.auto_allowed_journals:
                rec.with_context(group_allowed_journal_change=True).allowed_journal_ids = rec.group_id.active_allowed_journal_ids

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self._context.get("group_allowed_journal_change"):
            records.group_set_allowed_journals()
        return records
    