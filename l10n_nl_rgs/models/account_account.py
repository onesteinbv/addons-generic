# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"
    _order = "sort_code, code, placeholder_code"

    referentiecode = fields.Char()
    sort_code = fields.Char(string="Sorting code")

    def write(self, vals):
        resp = super().write(vals)

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
        for rec in self.filtered(
            lambda a: a.group_id and a.group_id.auto_allowed_journals
        ):
            rec.with_context(
                group_allowed_journal_change=True
            ).allowed_journal_ids = rec.group_id.active_allowed_journal_ids

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self._context.get("group_allowed_journal_change"):
            records.group_set_allowed_journals()
        return records
