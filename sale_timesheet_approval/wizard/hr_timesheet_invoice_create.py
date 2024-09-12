# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrTimesheetInvoiceCreate(models.TransientModel):
    _name = "hr.timesheet.invoice.create"
    _description = "Create invoice from timesheet"

    def do_approve(self):
        self.ensure_one()
        line_ids = self.env.context.get("active_ids")
        lines = (
            self.env["account.analytic.line"]
            .browse(line_ids)
            .filtered(lambda x: not x.is_approved)
        )
        lines.write({"is_approved": True})

    def do_create(self):
        self.ensure_one()
        line_ids = self.env.context.get("active_ids")
        lines = self.env["account.analytic.line"].browse(line_ids)
        lines.filtered(lambda x: not x.is_approved).write({"is_approved": True})
        sale_orders = lines.mapped("order_id")
        ctx = {
            "active_model": "sale.order",
            "active_ids": sale_orders.ids,
            "open_invoices": True,
            "timesheet_ids": line_ids,
        }
        payment = (
            self.env["sale.advance.payment.inv"]
            .with_context(ctx)
            .create(
                {
                    "advance_payment_method": "delivered",
                }
            )
        )

        return payment.create_invoices()
