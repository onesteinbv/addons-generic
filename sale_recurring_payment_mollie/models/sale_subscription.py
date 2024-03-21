import logging
from datetime import datetime

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def update_sale_subscription_payments_and_subscription_status(self, date_ref):
        # This method updates the subscription status/payments from mollie
        if self.payment_provider_subscription_id.provider_id.code != "mollie":
            return super().update_sale_subscription_payments_and_subscription_status(
                date_ref
            )
        mollie = self.env.ref("payment.payment_provider_mollie")
        payment_transaction_obj = self.env["payment.transaction"]
        mollie_client = mollie._api_mollie_get_client()
        mollie_customer_id = self.partner_id.mollie_customer_id
        if mollie_customer_id:
            customer = mollie_client.customers.get(mollie_customer_id)
            subscription = customer.subscriptions.get(
                self.payment_provider_subscription_id.reference
            )
            if subscription:
                if subscription.get("STATUS_CANCELED", False) and subscription.get(
                    "STATUS_CANCELED", ""
                ) == subscription.get("status", ""):
                    # As the subscription is cancelled, end the subscription
                    if "canceledAt" in subscription.keys():
                        cancelled_date = datetime.strptime(
                            subscription.get("canceledAt")[0:19], "%Y-%m-%dT%H:%M:%S"
                        ).date()
                    else:
                        cancelled_date = date_ref
                    vals = {
                        "date": cancelled_date,
                        "recurring_next_date": False,
                        "is_payment_provider_subscription_terminated": True,
                    }
                    stage = self.stage_id
                    closed_stage = self.env["sale.subscription.stage"].search(
                        [("type", "=", "post")], limit=1
                    )
                    if stage != closed_stage:
                        vals["stage_id"]: closed_stage.id
                    self.write(vals)
                    msg = _(
                        "The mollie subscription for this subscription has been terminated on %(cancelled_date)s",
                        cancelled_date=cancelled_date,
                    )
                    self.sudo().message_post(body=msg)
                subscription_payments = subscription.payments.list()
                if subscription_payments and subscription_payments.get("_embedded"):
                    payment_list = subscription_payments["_embedded"].get(
                        "payments", []
                    )
                    for payment in payment_list:
                        payment_transaction_obj._process_payment_provider_subscription_recurring_payment(
                            self, payment
                        )
        return True

    @api.model
    def terminate_payment_provider_subscription(self):
        # This method terminates the subscription on mollie
        if self.payment_provider_subscription_id.provider_id.code != "mollie":
            return super().terminate_payment_provider_subscription()
        else:
            vals = super().terminate_payment_provider_subscription()
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        customer = mollie_client.customers.get(self.partner_id.mollie_customer_id)
        subscription = customer.subscriptions.delete(
            self.payment_provider_subscription_id.reference
        )
        if subscription:
            cancelled_date = False
            if "canceledAt" in subscription.keys():
                cancelled_date = datetime.strptime(
                    subscription.get("canceledAt")[0:19], "%Y-%m-%dT%H:%M:%S"
                )
            msg = _(
                "The mollie subscription for this subscription has been terminated on %(cancelled_date)s",
                cancelled_date=cancelled_date,
            )
            self.sudo().message_post(body=msg)
        vals["is_payment_provider_subscription_terminated"] = True
        self.write(vals)
        return True
