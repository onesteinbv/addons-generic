# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _timesheet_domain_get_invoiced_lines(self, sale_line_delivery):
        """Only the selected timesheets should be invoiced"""
        domain = super(AccountMoveLine, self)._timesheet_domain_get_invoiced_lines(
            sale_line_delivery=sale_line_delivery
        )
        if self._context.get("timesheet_ids"):
            domain = [("id", "in", self._context["timesheet_ids"])] + domain
        return domain
