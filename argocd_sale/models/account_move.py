from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        self.filtered(
            lambda i: i.subscription_id
            and i.payment_state == "paid"
            and i.move_type == "out_invoice"
        ).mapped("subscription_id")._invoice_paid_hook()
        return super()._invoice_paid_hook()
