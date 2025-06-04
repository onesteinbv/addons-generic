from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        self.filtered(lambda i: i.subscription_id).mapped(
            "subscription_id"
        )._invoice_paid_hook()
        return super(AccountMove, self)._invoice_paid_hook()
