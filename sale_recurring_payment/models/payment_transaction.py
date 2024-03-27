from odoo import api, fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    payment_provider_subscription_id = fields.Many2one(
        "payment.provider.subscription",
        string="Payment Provider Subscription",
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
            and not self.invoice_ids[0].subscription_id.payment_provider_subscription_id
        )
        if not create_sub_for_sale_order and not create_sub_for_invoice:
            return res

        payment_data = self._provider_get_payment_data()
        if not self._must_create_subscription(payment_data):
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
        subscription_for_payment_provider = (
            self._create_subscription_for_payment_provider(subscription, payment_data)
        )
        payment_provider_subscription = self._create_payment_provider_subscription(
            subscription_for_payment_provider
        )
        subscription.payment_provider_subscription_id = payment_provider_subscription.id
        self.payment_provider_subscription_id = payment_provider_subscription.id

    def _provider_get_payment_data(self):
        self.ensure_one()
        return {}

    def _must_create_subscription(self, data):
        # This method needs to be extended in each provider module
        self.ensure_one()
        return False

    def _create_subscription_for_payment_provider(self, subscription, payment_data):
        # This method needs to be extended in each provider module.
        # We expect to receive a data structure containing the payment data;
        # We expect to return a data structure (depending on the payment provider implementation) describing the payment provider subscription
        self.ensure_one()
        return None

    def _create_payment_provider_subscription(self, subscription):
        # This method needs to be extended in each provider module.
        # We expect to receive the payment provider subscription;
        # This method processes them in order to create an Odoo payment.provider.subscription
        self.ensure_one()
        return self.env["payment.provider.subscription"]

    def _process_payment_provider_subscription_recurring_payment(
        self, subscription, payment
    ):
        # This method needs to be extended in each provider module.
        # This method should process payment transactions(recurring payments) for subscription invoices
        payment_transaction = self._get_payment_transaction(subscription, payment)
        done_payment_transaction = (
            payment_transaction.update_state_recurring_payment_transaction(
                subscription.payment_provider_subscription_id.provider_id, payment
            )
        )
        if done_payment_transaction:
            unpaid_invoices = subscription.invoice_ids.filtered(
                lambda i: i.payment_state == "not_paid"
            ).sorted("invoice_date")
            unpaid_invoice = unpaid_invoices and unpaid_invoices[0]
            if not unpaid_invoice:
                subscription.generate_invoice()
                unpaid_invoice = subscription.invoice_ids.filtered(
                    lambda i: i.payment_state == "not_paid"
                ).sorted("invoice_date")[0]
            done_payment_transaction.invoice_ids = [(6, 0, unpaid_invoice.ids)]
            done_payment_transaction._reconcile_after_done()
        return None

    def _get_payment_transaction(self, subscription, payment):
        # This method needs to be extended in each provider module.
        # This method should search for payment transaction if not found should create one with provided details
        return self.env["payment.transaction"]

    def _prepare_vals_for_recurring_payment_transaction_for_subscription(
        self, provider_reference, amount, subscription, currency
    ):
        # This method should return the vals for creating payment transactions
        vals = {
            "amount": amount,
            "currency_id": currency.id or subscription.currency_id.id,
            "provider_reference": provider_reference,
            "partner_id": subscription.partner_id.id,
            "payment_provider_subscription_id": subscription.payment_provider_subscription_id.id,
            "provider_id": subscription.payment_provider_subscription_id.provider_id.id,
        }
        return vals

    @api.returns("payment.transaction")
    def update_state_recurring_payment_transaction(self, provider, payment):
        # This method needs to be extended in each provider module.
        # This method should update the state of payment transactions and return done payment transactions if any
        return self.env["payment.transaction"]

    def _get_payment_transaction_by_provider_reference(
        self, provider_reference, provider_id
    ):
        # This method should search for payment transaction with provider reference provided
        return self.search(
            [
                ("provider_reference", "=", provider_reference),
                ("provider_id", "=", provider_id),
            ],
            limit=1,
        )
