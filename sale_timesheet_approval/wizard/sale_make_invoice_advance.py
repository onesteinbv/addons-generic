# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoices(self, sale_orders):
        """Override method from sale/wizard/sale_make_invoice_advance.py

        When the user wants to invoice only the selected timesheets to the SO
        then we need to recompute the qty_to_invoice for each product_id in
        sale.order.line,before creating the invoice.
        """
        if (
            self.advance_payment_method == "delivered"
            and self.invoicing_timesheet_enabled
        ):
            if self._context.get("timesheet_ids"):
                sale_orders.order_line.with_context(
                    self._context
                )._recompute_qty_to_invoice_based_on_selected_timesheets()

                return sale_orders.with_context(
                    timesheet_ids=self._context["timesheet_ids"]
                )._create_invoices(final=self.deduct_down_payments)

        return super()._create_invoices(sale_orders)
