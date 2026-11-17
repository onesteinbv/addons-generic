from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        eligible_invoices = self.filtered(
            lambda invoice: invoice.subscription_id
            and invoice.move_type == "out_invoice"
            and (
                invoice.payment_state == "paid"
                or (  # Consider invoices that are in payment but fully paid with done transactions
                    invoice.payment_state == "in_payment"
                    and invoice.currency_id.is_zero(invoice.amount_residual)
                    and invoice.transaction_ids.filtered(
                        lambda transaction: transaction.state == "done"
                        and transaction.operation not in ("refund", "validation")
                    )
                )
            )
        )
        eligible_invoices.mapped("subscription_id")._invoice_paid_hook()
        return super()._invoice_paid_hook()
