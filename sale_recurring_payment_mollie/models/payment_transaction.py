import logging

from odoo import _, models
from odoo.exceptions import ValidationError

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

    def _must_create_subscription(self, payment_data):
        # This method needs to be extended in each provider module
        if self.provider_code != "mollie":
            return super()._must_create_subscription(payment_data)

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

        mollie_customer_id = self._get_transaction_customer_id()
        if api_type == "order":
            payment_data["payment"]["customerId"] = mollie_customer_id
        else:
            payment_data["customerId"] = mollie_customer_id

        return payment_data, params

    def _create_subscription_for_payment_provider(self, subscription, payment_data):
        if self.provider_code != "mollie":
            return super()._create_subscription_for_payment_provider(payment_data)

        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        amount = {
            "currency": self.currency_id.name,
            "value": "%.2f" % (self.amount + self.fees),
        }
        subscription_template = subscription.template_id
        interval = "%s %s" % (
            subscription_template.recurring_interval,
            subscription_template.recurring_rule_type,
        )
        description = subscription.name
        # webhook_url = urls.url_join(mollie.get_base_url(), MollieController._webhook_url)
        mollie_customer_id = self._get_transaction_customer_id()
        customer = mollie_client.customers.get(mollie_customer_id)

        data = {
            "amount": amount or "",
            "interval": interval or "",
            "description": description or "",
            # 'webhookUrl': webhook_url,
            "startDate": subscription.recurring_next_date.strftime("%Y-%m-%d"),
            "mandateId": payment_data and payment_data["mandateId"] or "",
        }
        try:
            subscription = customer.subscriptions.create(
                data
            )  # Uncomment this when ready (issue is that localhost doesn't work with Mollie)
        except Exception as e:
            raise ValidationError(_(str(e))) from e
        # subscription = {'resource': 'subscription', 'subscriptions_id': 'Test ID: %s' % (datetime.datetime.now())}

        return subscription

    def _provider_get_payment_data(self):
        if self.provider_code != "mollie":
            return super()._provider_get_payment_data()
        return self.provider_id._api_mollie_get_payment_data(self.provider_reference)

    def _create_payment_provider_subscription(self, subscription):
        res = super()._create_payment_provider_subscription(subscription)
        if self.provider_code == "mollie":
            res = self.env["payment.provider.subscription"].create(
                {"reference": subscription["id"], "provider_id": self.provider_id.id}
            )
        return res

    def _get_payment_transaction(self, subscription, payment):
        payment_transaction = super()._get_payment_transaction(subscription, payment)
        if subscription.payment_provider_subscription_id.provider_id.code == "mollie":
            payment_transaction = self._get_payment_transaction_by_provider_reference(
                payment["id"],
                subscription.payment_provider_subscription_id.provider_id.id,
            )
            if not payment_transaction:
                provider_reference = payment["id"]
                amount = payment.get("amount", {}).get("value", 0.0)
                currency = (
                    self.env["res.currency"].search(
                        [("name", "=", payment.get("amount", {}).get("currency", ""))],
                        limit=1,
                    )
                    if payment.get("amount", {}).get("currency", "")
                    else subscription.currency_id
                )
                payment_transaction = self.create(
                    self._prepare_vals_for_recurring_payment_transaction_for_subscription(
                        provider_reference, amount, subscription, currency
                    )
                )
        return payment_transaction

    def update_state_recurring_payment_transaction(self, provider, payment):
        payment_transaction = super()._get_payment_transaction(provider, payment)
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
