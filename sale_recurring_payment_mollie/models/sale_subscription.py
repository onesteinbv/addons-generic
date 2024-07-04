import logging

from odoo import _, api, fields, models

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
        if mollie_customer_id:
            customer = mollie_client.customers.get(mollie_customer_id)
            mandate = customer.mandates.get(self.payment_provider_mandate_id.reference)
            if mandate:
                invoices = self.invoice_ids.filtered(
                    lambda i: i.invoice_date == date_ref
                )
                if not invoices:
                    self.generate_invoice()
                    unpaid_invoice = self.invoice_ids.filtered(
                        lambda i: i.invoice_date == date_ref
                        and i.payment_state == "not_paid"
                    )
                else:
                    unpaid_invoice = invoices.filtered(
                        lambda i: i.payment_state == "not_paid"
                    )
                if unpaid_invoice:
                    payment_transaction_obj._process_payment_provider_recurring_payment(
                        self, unpaid_invoice
                    )
        return True

    @api.model
    def terminate_payment_provider_mandate(self):
        # This method terminates the mandate on mollie
        if self.payment_provider_mandate_id.provider_id.code != "mollie":
            return super().terminate_payment_provider_mandate()
        else:
            vals = super().terminate_payment_provider_mandate()
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        customer = mollie_client.customers.get(self.partner_id.mollie_customer_id)
        customer.mandates.delete(self.payment_provider_mandate_id.reference)
        cancelled_date = fields.Date.context_today(self)
        msg = _(
            "The mollie mandate for this subscription has been terminated on %(cancelled_date)s",
            cancelled_date=cancelled_date,
        )
        self.sudo().message_post(body=msg)
        vals["is_payment_provider_mandate_terminated"] = True
        self.write(vals)
        return True
