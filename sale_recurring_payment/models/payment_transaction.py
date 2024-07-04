from odoo import api, fields, models
from odoo.fields import Command


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    payment_provider_mandate_id = fields.Many2one(
        "payment.provider.mandate",
        string="Payment Provider Mandate",
        readonly=True,
    )

    def _process_notification_data(self, data):
        # If the transaction concerns a subscription SO, which was not processed yet and which doesn't have a related subscription yet,
        # depending on the data we receive (to be interpreted specifically for the provider of the transaction) we may want to
        # get it confirmed and create a subscription (functionality to create a subscription from the SO is provided in OCA module subscription_oca).
        self.ensure_one()
        res = super(PaymentTransaction, self)._process_notification_data(data)
        create_sub_for_sale_order = (
            self.sale_order_ids
            and self.sale_order_ids[0].group_subscription_lines()
            and not self.sale_order_ids[0].subscriptions_count
        )
        create_sub_for_invoice = (
            self.invoice_ids
            and self.invoice_ids[0].subscription_id
            and not self.invoice_ids[0].subscription_id.payment_provider_mandate_id
        )
        if not create_sub_for_sale_order and not create_sub_for_invoice:
            return res

        payment_data = self._provider_get_payment_data()
        if not self._must_create_mandate(payment_data):
            return res

        if create_sub_for_sale_order:
            sale_order = self.sale_order_ids[0]
            sale_order.action_confirm()
            subscription = sale_order.subscription_ids[0]
            invoice = sale_order._create_invoices()
            subscription.invoice_ids = [(4, invoice.id)]
            self.invoice_ids = [(6, 0, invoice.ids)]
        else:  # We are already sure create_sub_for_invoice is truthy because of earlier statements
            invoice = self.invoice_ids[0]
            subscription = invoice.subscription_id
        # pylint: disable=assignment-from-none
        mandate_for_payment_provider = self._get_mandate_reference_for_payment_provider(
            payment_data
        )
        payment_provider_mandate = self._create_payment_provider_mandate(
            mandate_for_payment_provider
        )
        subscription.payment_provider_mandate_id = payment_provider_mandate.id
        self.payment_provider_mandate_id = payment_provider_mandate.id

    def _provider_get_payment_data(self):
        self.ensure_one()
        return {}

    def _must_create_mandate(self, data):
        # This method needs to be extended in each provider module
        self.ensure_one()
        return False

    def _get_mandate_reference_for_payment_provider(self, payment):
        # This method needs to be extended in each provider module
        self.ensure_one()
        return False

    def _create_payment_provider_mandate(self, mandate_reference):
        # We expect to receive the payment provider mandate reference;
        # This method processes them in order to create an Odoo payment.provider.mandate
        return self.env["payment.provider.mandate"].create(
            {"reference": mandate_reference, "provider_id": self.provider_id.id}
        )

    def _process_payment_provider_recurring_payment(self, subscription, invoice):
        # This method needs to be extended in each provider module.
        # This method should process payment transactions(recurring payments) for subscription invoices
        payment_transaction = self._get_payment_transaction_by_mandate_id_for_invoice(
            invoice.id,
            subscription.payment_provider_mandate_id.id,
        )
        return payment_transaction

    def create_provider_recurring_payment(self, subscription):
        # This method needs to be extended in each provider module.
        # This method should create recurring payments at the provider end
        # We expect to receive a data structure containing the payment data(depending on the payment provider implementation)
        return None

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

    def _get_payment_transaction_by_mandate_id_for_invoice(
        self, invoice_id, payment_provider_mandate_id
    ):
        # This method should search for payment transaction with payment_provider_mandate_id and invoice provided
        return self.search(
            [
                ("payment_provider_mandate_id", "=", payment_provider_mandate_id),
                ("invoice_ids", "in", invoice_id),
            ],
            limit=1,
        )
