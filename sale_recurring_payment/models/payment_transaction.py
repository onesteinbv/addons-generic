from odoo import api, fields, models
from odoo.fields import Command


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    payment_provider_mandate_id = fields.Many2one(
        "payment.provider.mandate",
        string="Mandate",
        readonly=True,
    )

    @api.model
    def _create_payment_provider_mandate(self, reference):
        """Shortcut to create a mandate"""
        return self.env["payment.provider.mandate"].create(
            {
                "reference": reference,
                "provider_id": self.provider_id.id,
                "partner_id": self.partner_id.id,
            }
        )

    def _process_payment_provider_recurring_payment(self, subscription, invoice):
        payment_transaction = self.search(
            [
                (
                    "payment_provider_mandate_id",
                    "=",
                    subscription.payment_provider_mandate_id.id,
                ),
                ("invoice_ids", "in", invoice.id),
            ],
            limit=1,
        )
        if not payment_transaction:
            payment_transaction = self.create(
                self._prepare_vals_for_recurring_payment_transaction_for_subscription(
                    invoice, subscription
                )
            )
            (
                payment,
                provider_reference,
            ) = payment_transaction.create_provider_recurring_payment(subscription)
            payment_transaction.write({"provider_reference": provider_reference})
            done_payment_transaction = (
                payment_transaction.update_state_recurring_payment_transaction(
                    subscription.payment_provider_mandate_id.provider_id, payment
                )
            )
            if done_payment_transaction:
                done_payment_transaction._reconcile_after_done()
        return payment_transaction

    def create_provider_recurring_payment(self, subscription):
        # This method needs to be extended in each provider module.
        # This method should create recurring payments at the provider end
        # We expect to receive a data structure containing the payment data(depending on the payment provider implementation)
        return None, None

    def _prepare_vals_for_recurring_payment_transaction_for_subscription(
        self, invoice, subscription
    ):
        # This method should return the vals for creating payment transactions
        vals = {
            "amount": invoice.amount_residual,
            "currency_id": subscription.currency_id.id,
            "partner_id": subscription.partner_id.id,
            "payment_provider_mandate_id": subscription.payment_provider_mandate_id.id,
            "provider_id": subscription.payment_provider_mandate_id.provider_id.id,
            "invoice_ids": [Command.set([invoice.id])],
        }
        return vals

    @api.returns("payment.transaction")
    def update_state_recurring_payment_transaction(self, provider, payment):
        # This method needs to be extended in each provider module.
        # This method should update the state of payment transactions and return done payment transactions if any
        return self.env["payment.transaction"]
