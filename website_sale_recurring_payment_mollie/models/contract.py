import logging
from datetime import datetime

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class ContractContract(models.Model):
    _inherit = "contract.contract"

    def update_contract_payments_and_subscription_status(self, date_ref):
        if self.contract_payment_subscription_id.provider_id.code != "mollie":
            return super().update_contract_payments_and_subscription_status(date_ref)
        mollie = self.env.ref("payment.payment_provider_mollie")
        payment_transaction_obj = self.env["payment.transaction"]
        mollie_client = mollie._api_mollie_get_client()
        mollie_customer_id = self.partner_id.mollie_customer_id
        if mollie_customer_id:
            customer = mollie_client.customers.get(mollie_customer_id)
            subscription = customer.subscriptions.get(
                self.contract_payment_subscription_id.reference
            )
            if subscription:
                if subscription.get("STATUS_CANCELED", False) and subscription.get(
                    "STATUS_CANCELED", ""
                ) == subscription.get("status", ""):
                    # As the subscription is cancelled, end the contract
                    if "canceledAt" in subscription.keys():
                        canceled_date = datetime.strptime(
                            subscription.get("canceledAt")[0:19], "%Y-%m-%dT%H:%M:%S"
                        ).date()
                    else:
                        canceled_date = date_ref
                    self.date_end = canceled_date
                subscription_payments = subscription.payments.list()
                if subscription_payments and subscription_payments.get("_embedded"):
                    payment_list = subscription_payments["_embedded"].get(
                        "payments", []
                    )
                    for payment in payment_list:
                        payment_transaction_obj._process_subscription_recurring_payment(
                            self, payment
                        )
        return True

    @api.model
    def terminate_provider_subscription(self):
        if self.contract_payment_subscription_id.provider_id.code != "mollie":
            return super().terminate_provider_subscription()
        mollie = self.env.ref("payment.payment_provider_mollie")
        try:
            mollie_client = mollie._api_mollie_get_client()
            customer = mollie_client.customers.get(self.partner_id.mollie_customer_id)
            subscription = customer.subscriptions.delete(
                self.contract_payment_subscription_id.reference
            )
            if subscription:
                canceled_date = False
                if "canceledAt" in subscription.keys():
                    canceled_date = datetime.strptime(
                        subscription.get("canceledAt")[0:19], "%Y-%m-%dT%H:%M:%S"
                    )
                msg = _(
                    "<b>The mollie subscription for this contract has been terminated on %s.</b>",
                    canceled_date,
                )
                self.sudo().message_post(body=msg)
        except Exception:
            _logger.info(_("Mollie customer or subscription not found"))
        self.is_provider_subscription_terminated = True
        return True
