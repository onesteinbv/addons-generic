import logging
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_mollie.controllers.main import MollieController

_logger = logging.getLogger(__name__)

RULE_TYPE_MAP = {
    "daily": (1, "days"),
    "weekly": (1, "weeks"),
    "monthly": (1, "months"),
    "monthlylastday": (1, "months"),
    "quarterly": (3, "months"),
    "semesterly": (6, "months"),
    "yearly": (12, "months"),
}


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_transaction_customer_id(self):
        mollie_customer_id = False
        if self.sale_order_ids:
            partner_obj = self.sale_order_ids[0].partner_id
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

    def _must_create_contract(self, payment_data):
        # This method needs to be extended in each provider module
        if self.provider_code != "mollie":
            return super()._must_create_contract(payment_data)

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
            self.sale_order_ids.is_contract
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
            payment_data.update(
                {
                    "description": f"First payment for {self.sale_order_ids.name} / {self.sale_order_ids.order_line.product_id.name}",
                    "sequenceType": "first",
                }
            )

        mollie_customer_id = self._get_transaction_customer_id()
        if api_type == "order":
            payment_data["payment"]["customerId"] = mollie_customer_id
        else:
            payment_data["customerId"] = mollie_customer_id

        return payment_data, params

    def _create_provider_subscription(self, payment_data):
        if self.provider_code != "mollie":
            return super()._create_provider_subscription(payment_data)

        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()

        contract = self.sale_order_ids[0].mapped("order_line.contract_id")[0]
        amount = {
            "currency": self.currency_id.name,
            "value": "%.2f" % (self.amount + self.fees),
        }
        contract_line = contract.contract_line_ids[0]
        interval = "%s %s" % (
            contract_line.recurring_interval
            * RULE_TYPE_MAP[contract_line.recurring_rule_type][0],
            RULE_TYPE_MAP[contract_line.recurring_rule_type][1],
        )
        description = contract.name
        webhook_url = urls.url_join(
            mollie.get_base_url(), MollieController._webhook_url
        )
        mollie_customer_id = self._get_transaction_customer_id()
        customer = mollie_client.customers.get(mollie_customer_id)

        data = {
            "amount": amount or "",
            "interval": interval or "",
            "description": description or "",
            "webhookUrl": webhook_url,
            "startDate": self._get_start_date(contract_line),
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

    def _create_contract_payment_subscription(self, subscription):
        res = super()._create_contract_payment_subscription(subscription)
        if self.provider_code == "mollie":
            res = self.env["contract.payment.subscription"].create(
                {"reference": subscription["id"], "provider_id": self.provider_id.id}
            )
        return res

    def _get_payment_transaction(self, contract, payment):
        payment_transaction = super()._get_payment_transaction(contract, payment)
        if contract.contract_payment_subscription_id.provider_id.code == "mollie":
            payment_transaction = self._get_payment_transaction_by_provider_reference(
                payment["id"], contract.contract_payment_subscription_id.provider_id.id
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
                    else contract.currency_id
                )
                payment_transaction = self.create(
                    self._prepare_vals_for_recurring_payment_transaction_for_subscription(
                        provider_reference, amount, contract, currency
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

    def _get_start_date(self, contract_line):
        start_date = date.today()
        sub_inter = (
            contract_line.recurring_interval
            * RULE_TYPE_MAP[contract_line.recurring_rule_type][0]
        )
        if RULE_TYPE_MAP[contract_line.recurring_rule_type][1] == "days":
            start_date = date.today() + timedelta(days=int(sub_inter))
        elif RULE_TYPE_MAP[contract_line.recurring_rule_type][1] == "months":
            start_date = date.today() + relativedelta(months=int(sub_inter))
        elif RULE_TYPE_MAP[contract_line.recurring_rule_type][1] == "weeks":
            start_date = date.today() + relativedelta(weeks=int(sub_inter))
        return start_date.strftime("%Y-%m-%d")
