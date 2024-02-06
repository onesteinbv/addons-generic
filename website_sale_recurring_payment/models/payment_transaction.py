from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    contract_payment_subscription_id = fields.Many2one(
        "contract.payment.subscription",
        string="Contract Payment Subscription",
        readonly=True,
    )

    def _process_notification_data(self, data):
        # If the transaction concerns a contract SO, which was not processed yet and which doesn't have a related contract yet,
        # depending on the data we receive (to be interpreted specifically for the provider of the transaction) we may want to
        # get it confirmed and create a contract (functionality to create a contract from the SO is provided in OCA module product_contract).
        self.ensure_one()
        if (
            self.sale_order_ids
            and self.sale_order_ids[0].is_contract
            and not self.sale_order_ids[0].contract_count
        ):
            payment_data = self._provider_get_payment_data()
            if self._must_create_contract(payment_data):
                self.sale_order_ids[0].action_create_contract()
                contract = self.sale_order_ids[0].mapped("order_line.contract_id")[0]
                contract.line_recurrence = True
                contract.contract_line_ids.date_end = False
                subscription = self._create_provider_subscription(payment_data)
                contract_payment_subscription = (
                    self._create_contract_payment_subscription(subscription)
                )
                contract.contract_payment_subscription_id = (
                    contract_payment_subscription.id
                )
                self.contract_payment_subscription_id = contract_payment_subscription.id
                invoice = contract.recurring_create_invoice()
                self.invoice_ids = [(6, 0, invoice.ids)]
        return super(PaymentTransaction, self)._process_notification_data(data)

    def _provider_get_payment_data(self):
        self.ensure_one()
        return {}

    def _must_create_contract(self, data):
        # This method needs to be extended in each provider module
        self.ensure_one()
        return False

    def _create_provider_subscription(self, payment_data):
        # This method needs to be extended in each provider module.
        # We expect to receive a data structure containing the payment data;
        # We expect to return a data structure (depending from the provider implementation) describing the provider subscription
        self.ensure_one()
        return {}

    def _create_contract_payment_subscription(self, subscription):
        # This method needs to be extended in each provider module.
        # We expect to receive the provider subscription;
        # This method processes them in order to create an Odoo contract.payment.subscription
        self.ensure_one()
        return self.env["contract.payment.subscription"]

    def _process_subscription_recurring_payment(self, contract, payment):
        # This method needs to be extended in each provider module.
        # This method should process payment transaction(recurring payment) for contract invoices
        payment_transaction = self._get_payment_transaction(contract, payment)
        done_payment_transaction = (
            payment_transaction.update_state_recurring_payment_transaction(
                contract.contract_payment_subscription_id.provider_id, payment
            )
        )
        if done_payment_transaction:
            contract_invoices = contract._get_related_invoices()
            unpaid_invoice = self.env["account.move"]
            for invoice in contract_invoices:
                if invoice.payment_state == "not_paid":
                    unpaid_invoice = invoice
                    continue
            if not unpaid_invoice:
                unpaid_invoice = contract.recurring_create_invoice()
            done_payment_transaction.invoice_ids = [(6, 0, unpaid_invoice.ids)]
            done_payment_transaction._reconcile_after_done()
        return None

    def _get_payment_transaction(self, contract, payment):
        # This method needs to be extended in each provider module.
        # This method should search for payment transaction if not found should create one with provided details
        return self.env["payment.transaction"]

    def _prepare_vals_for_recurring_payment_transaction_for_subscription(
        self, provider_reference, amount, contract, currency
    ):
        # This method should return the vals for creating payment transactions
        vals = {
            "amount": amount,
            "currency_id": currency.id or contract.currency_id.id,
            "provider_reference": provider_reference,
            "partner_id": contract.partner_id.id,
            "contract_payment_subscription_id": contract.contract_payment_subscription_id.id,
            "provider_id": contract.contract_payment_subscription_id.provider_id.id,
        }
        return vals

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
