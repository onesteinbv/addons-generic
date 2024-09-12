# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrTimesheetInvoiceCreate(models.TransientModel):
    _inherit = "hr.timesheet.invoice.create"

    def do_approve(self):
        res = super().do_approve()
        line_ids = self.env.context.get("active_ids")
        lines = (
            self.env["account.analytic.line"]
            .browse(line_ids)
            .filtered(lambda x: not x.is_non_billable)
        )
        lines.write({"is_non_billable": True})
        return res
