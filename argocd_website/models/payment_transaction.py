from odoo import Command, fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    application_subscription_id = fields.Many2one(
        comodel_name="sale.subscription",
        index="btree_not_null",
        ondelete="set null",
    )

    def _post_process(self):
        for transaction in self.filtered(
            lambda tx: tx.state == "done"
            and tx.application_subscription_id
            and tx.application_subscription_id.stage_id.type == "initial_payment"
            and not tx.invoice_ids
        ):
            subscription = transaction.application_subscription_id
            if not subscription.invoice_ids:
                subscription.recurring_next_date = fields.Date.today()
                subscription.generate_invoice()

            invoices = subscription.invoice_ids
            invoices.ensure_one()
            transaction.invoice_ids = [Command.set(invoices.ids)]

        return super()._post_process()
