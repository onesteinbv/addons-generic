# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    is_approved = fields.Boolean()

    def action_unapprove(self):
        if self.filtered(lambda x: x.timesheet_invoice_id):
            raise ValidationError(
                _("You cannot unapprove a timesheet line already invoiced")
            )
        self.write({"is_approved": False})
