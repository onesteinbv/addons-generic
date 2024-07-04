import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_transaction_customer_id(self):
        mollie_customer_id = False
        if self.sale_order_ids or self.invoice_ids:
            partner_obj = (
                self.invoice_ids
                and self.invoice_ids[0].partner_id
                or self.sale_order_ids
                and self.sale_order_ids[0].partner_id
            )
            if partner_obj.mollie_customer_id:
                mollie_customer_id = partner_obj.mollie_customer_id
            else:
                customer_id_data = self.provider_id.with_context(
                    partner=partner_obj.id
                )._api_mollie_create_customer_id()
                if customer_id_data and customer_id_data.get("id"):
                    mollie_customer_id = customer_id_data.get("id")
                    partner_obj.write({"mollie_customer_id": mollie_customer_id})
        return mollie_customer_id

    def _must_create_mandate(self, payment_data):
        # This method needs to be extended in each provider module
        if self.provider_code != "mollie":
            return super()._must_create_mandate(payment_data)
        payment_status = payment_data.get("status")
        if payment_status == "paid":
            return True
        return False

    def _process_notification_data(self, data):
        if self.provider_code != "mollie":
            return super()._process_notification_data(data)
        self._process_refund_transactions_status()
        if not self.state == "done":
            return super()._process_notification_data(data)

    def _create_mollie_order_or_payment(self):
        self.ensure_one()
        method_record = self.provider_id.mollie_methods_ids.filtered(
            lambda m: m.method_code == self.mollie_payment_method
        )
        if (
            (self.sale_order_ids and self.sale_order_ids.group_subscription_lines())
            or (self.invoice_ids and self.invoice_ids.subscription_id)
            and method_record.supports_payment_api
            and method_record.supports_order_api
        ):
            result = self.with_context(
                first_mollie_payment=True
            )._mollie_create_payment_record("payment")
            return result
        else:
            return super(PaymentTransaction, self)._create_mollie_order_or_payment()

    def _mollie_prepare_payment_payload(self, api_type):
        payment_data, params = super(
            PaymentTransaction, self
        )._mollie_prepare_payment_payload(api_type)

        if self._context.get("first_mollie_payment"):
            name = (
                self.sale_order_ids
                and self.sale_order_ids.name
                or self.invoice_ids
                and self.invoice_ids.name
            )
            payment_data.update(
                {
                    "description": f"First payment for {name}",
                    "sequenceType": "first",
                }
            )
        if self._context.get("recurring_mollie_payment"):
            name = (
                self.sale_order_ids
                and self.sale_order_ids.name
                or self.invoice_ids
                and self.invoice_ids.name
            )
            payment_data.update(
                {
                    "description": f"Payment for {name}",
                    "sequenceType": "recurring",
                    "mandateId": self._context.get("mandate_id"),
                }
            )
        mollie_customer_id = self._get_transaction_customer_id()
        if api_type == "order":
            payment_data["payment"]["customerId"] = mollie_customer_id
        else:
            payment_data["customerId"] = mollie_customer_id

        return payment_data, params

    def _get_mandate_reference_for_payment_provider(self, payment):
        if self.provider_code != "mollie":
            return super()._get_mandate_reference_for_payment_provider(payment)
        return payment and payment["mandateId"] or ""

    def _provider_get_payment_data(self):
        if self.provider_code != "mollie":
            return super()._provider_get_payment_data()
        return self.provider_id._api_mollie_get_payment_data(self.provider_reference)

    def _process_payment_provider_recurring_payment(self, subscription, invoice):
        payment_transaction = super()._process_payment_provider_recurring_payment(
            subscription, invoice
        )
        if not payment_transaction:
            if subscription.payment_provider_mandate_id.provider_id.code == "mollie":
                payment_transaction = self.create(
                    self._prepare_vals_for_recurring_payment_transaction_for_subscription(
                        invoice, subscription
                    )
                )
                payment = payment_transaction.create_provider_recurring_payment(
                    subscription
                )
                payment_transaction.write({"provider_reference": payment["id"]})
                done_payment_transaction = (
                    payment_transaction.update_state_recurring_payment_transaction(
                        subscription.payment_provider_mandate_id.provider_id, payment
                    )
                )
                if done_payment_transaction:
                    done_payment_transaction._reconcile_after_done()
        return payment_transaction

    def create_provider_recurring_payment(self, subscription):
        provider_payment = super().create_provider_recurring_payment(subscription)
        if subscription.payment_provider_mandate_id.provider_id.code == "mollie":
            mollie = self.env.ref("payment.payment_provider_mollie")
            mollie_client = mollie._api_mollie_get_client()
            mollie_payment_vals, params = self.with_context(
                recurring_mollie_payment=True,
                mandate_id=subscription.payment_provider_mandate_id.reference,
            )._mollie_prepare_payment_payload("payment")
            mollie_payment_vals.pop("redirectUrl")
            mollie_payment_vals.pop("method")
            mollie_payment_vals.pop("customerId")
            customer = mollie_client.customers.get(self.partner_id.mollie_customer_id)
            provider_payment = customer.payments.create(mollie_payment_vals)
        return provider_payment

    def update_state_recurring_payment_transaction(self, provider, payment):
        payment_transaction = super().update_state_recurring_payment_transaction(
            provider, payment
        )
        if provider.code == "mollie":
            payment_status = payment.get("status")
            if payment_status == "paid":
                payment_transaction = self._set_done()
            elif payment_status == "pending":
                self._set_pending()
            elif payment_status == "authorized":
                self._set_authorized()
            elif payment_status in ["expired", "canceled", "failed"]:
                self._set_canceled(
                    "Mollie: " + _("Mollie: canceled due to status: %s", payment_status)
                )
            elif payment_status == "open":
                self._set_error(
                    "Mollie: "
                    + _("A payment was started, but not finished: %s", payment_status)
                )
            else:
                _logger.info(
                    "Received data with invalid payment status: %s", payment_status
                )
                self._set_error(
                    "Mollie: "
                    + _("Received data with invalid payment status: %s", payment_status)
                )
        return payment_transaction
