# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("analytic_line_ids.is_approved")
    def _compute_qty_delivered(self):
        return super(SaleOrderLine, self)._compute_qty_delivered()

    def _timesheet_compute_delivered_quantity_domain(self):
        """Non approved timesheets should not be considered"""
        domain = super(
            SaleOrderLine, self
        )._timesheet_compute_delivered_quantity_domain()
        domain += [("is_approved", "=", True)]
        return domain

    def _recompute_qty_to_invoice_based_on_selected_timesheets(self):
        """Recompute the qty_to_invoice field for product containing timesheets

        Search the existed timesheets as per the timesheets in context in parameter.
        Retrieve the unit_amount of this timesheet and then recompute
        the qty_to_invoice for each current product.
        """
        lines_by_timesheet = self.filtered(
            lambda sol: sol.product_id and sol.product_id._is_delivered_timesheet()
        )
        domain = lines_by_timesheet._timesheet_compute_delivered_quantity_domain()
        refund_account_moves = self.order_id.invoice_ids.filtered(
            lambda am: am.state == "posted" and am.move_type == "out_refund"
        ).reversed_entry_id
        timesheet_domain = [
            "|",
            ("timesheet_invoice_id", "=", False),
            ("timesheet_invoice_id.state", "=", "cancel"),
        ]
        if refund_account_moves:
            credited_timesheet_domain = [
                ("timesheet_invoice_id.state", "=", "posted"),
                ("timesheet_invoice_id", "in", refund_account_moves.ids),
            ]
            timesheet_domain = expression.OR(
                [timesheet_domain, credited_timesheet_domain]
            )
        domain = expression.AND([domain, timesheet_domain])
        if self._context.get("timesheet_ids"):
            domain = expression.AND(
                [domain, [("id", "in", self._context["timesheet_ids"])]]
            )
        mapping = lines_by_timesheet.sudo()._get_delivered_quantity_by_analytic(domain)
        for line in lines_by_timesheet:
            qty_to_invoice = mapping.get(line.id, 0.0)
            if qty_to_invoice:
                line.qty_to_invoice = qty_to_invoice
            else:
                prev_inv_status = line.invoice_status
                line.qty_to_invoice = qty_to_invoice
                line.invoice_status = prev_inv_status
