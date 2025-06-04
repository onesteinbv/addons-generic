import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def update_sale_subscription_payments(self, date_ref):
        # This method updates the payments and their status for mollie
        if self.payment_provider_mandate_id.provider_id.code != "mollie":
            return super().update_sale_subscription_payments(date_ref)
        mollie = self.env.ref("payment.payment_provider_mollie")
        payment_transaction_obj = self.env["payment.transaction"]
        mollie_client = mollie._api_mollie_get_client()
        mollie_customer_id = self.partner_id.mollie_customer_id
        if not mollie_customer_id:
            return False
        customer = mollie_client.customers.get(mollie_customer_id)
        mandate = customer.mandates.get(self.payment_provider_mandate_id.reference)
        if not mandate:
            return False
        invoices = self.invoice_ids.filtered(lambda i: i.invoice_date == date_ref)
        if not invoices and date_ref == self.recurring_next_date:
            self.generate_invoice()
        unpaid_invoice = self.invoice_ids.filtered(
            lambda i: i.invoice_date == date_ref
            and i.payment_state == "not_paid"  # TODO: Do we need to check here on date?
        )
        if not unpaid_invoice:
            return False
        payment_transaction_obj._process_payment_provider_recurring_payment(
            self, unpaid_invoice
        )
        return True
