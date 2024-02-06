# Copyright 2017-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("display_type", "company_id")
    def _compute_account_id(self):
        res = super()._compute_account_id()
        for line in self.filtered(
            lambda l: l.display_type not in ("line_section", "line_note")
            and l.move_id.is_invoice()
        ):
            partner = line.move_id.partner_id
            if partner and partner.partner_default_account_id:
                company_acc = partner.partner_default_account_id.company_id
                if partner.company_id == company_acc or not partner.company_id:
                    line.account_id = partner.partner_default_account_id
        return res

    @api.model
    def default_get(self, default_fields):
        values = super().default_get(default_fields)

        if "account_id" in default_fields and values.get("partner_id"):
            # Override 'account_id'.
            partner = self.env["res.partner"].browse(values["partner_id"])
            if partner.partner_default_account_id:
                values["account_id"] = partner.partner_default_account_id.id

        return values
