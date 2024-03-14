import logging
from datetime import datetime

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MolliePayment(models.Model):
    _name = "mollie.payment"
    _description = "Mollie Payment"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Payment", readonly=True, required=True, copy=False, default="New"
    )
    payment_id = fields.Char(help="Mollie Payment ID")
    createdAt = fields.Datetime(string="Date")
    amount = fields.Float(tracking=1)
    amount_currency = fields.Char(string="Currency")
    description = fields.Text()
    method = fields.Char()
    metadata = fields.Text()
    status = fields.Char(tracking=1)
    paid_date = fields.Datetime(tracking=1)
    profileId = fields.Char(string="Profile ID")
    customerId = fields.Char(string="Customer ID")
    mandateId = fields.Char(string="Mandate ID", tracking=1)
    subscription_id = fields.Char(string="Subscription ID", tracking=1)
    sequence_type = fields.Char(string="Type", tracking=1)
    settlement_amount = fields.Float(tracking=1)
    settlement_currency = fields.Char()
    details = fields.Text()
    mollie_subscription_id = fields.Many2one(
        "mollie.subscription", string="Subscription", tracking=1
    )
    checkout_url = fields.Text(string="Checkout URL", tracking=1)
    invoice_id = fields.Many2one("account.move")
    transaction_id = fields.Many2one("payment.transaction")

    def _get_payment_obj(self, payment_id):
        """Get payment data from odoo"""
        payment_obj = self.sudo().search([("payment_id", "=", payment_id)])
        return payment_obj if payment_obj else {}

    def refresh_payment(self):
        """Reload payment data using API"""
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        pay_obj = mollie_client.payments.get(self.payment_id)
        if pay_obj:
            self._update_payment(pay_obj, self.env.user.name)

    def _update_payment(self, pay_obj, method):
        """Update payment record from payment data"""
        if pay_obj:
            paid_date = datetime.strptime(
                pay_obj["createdAt"][0:19], "%Y-%m-%dT%H:%M:%S"
            )
            if pay_obj.get("paidAt", False):
                paid_date = datetime.strptime(
                    pay_obj["paidAt"][0:19], "%Y-%m-%dT%H:%M:%S"
                )
            vals = {
                "amount": pay_obj["amount"] and pay_obj["amount"]["value"] or False,
                "amount_currency": pay_obj.get("amount", {}).get("currency", ""),
                "metadata": pay_obj["metadata"] or False,
                "status": pay_obj["status"] or False,
                "paid_date": paid_date or False,
                "settlement_amount": pay_obj.get("settlementAmount", {}).get(
                    "value", 0.0
                ),
                "settlement_currency": pay_obj.get("settlementAmount", {}).get(
                    "currency", 0.0
                ),
                "details": pay_obj.get("details", False),
                "transaction_id": pay_obj["metadata"]
                and pay_obj.get("metadata", {}).get("transaction_id"),
            }
            if pay_obj.get("subscriptionId", False):
                vals.update({"subscription_id": pay_obj.get("subscriptionId")})
            self.sudo().write(vals)
            msg = "<b>This payment has been updated by %s on %s" % (
                method,
                datetime.today().strftime("%Y-%m-%d %H:%M"),
            )
            for obj in self:
                obj.sudo().message_post(body=msg)

    def auto_update_payments(self):
        """Cron job for update and create a payment records from Mollie API"""
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        subscription_objs = self.env["mollie.subscription"].search(
            [("status", "=", "active")]
        )
        customer_ids = list(set(subscription_objs.mapped("customerId")))
        for customer_id in customer_ids:
            customer = mollie_client.customers.get(customer_id)
            payments = customer.payments.list()
            if payments and payments.get("_embedded"):
                payment_list = payments["_embedded"].get("payments", [])
                for payment in payment_list:
                    payment_objs = self.sudo()._get_payment_obj(payment["id"])
                    if payment_objs:
                        payment_obj = payment_objs.filtered(
                            lambda l: l.status
                            not in ["paid", "expired", "canceled", "failed"]
                        )
                        if payment_obj and payment_obj.status != payment["status"]:
                            payment_obj.sudo()._update_payment(
                                payment, self.env.user.name
                            )
                    else:
                        self.sudo()._create_payment(payment)

    def pay_mollie_invoice(self):
        """
        Register payment for the related invoice.
        @author: Maulik Barad on Date 01-Dec-2022.
        """
        vals = self._prepare_payment_dict(self.invoice_id)
        payment = self.env["account.payment"].create(vals)
        payment.action_post()
        self.reconcile_payment_ept(payment, self.invoice_id)
        return True

    def _prepare_payment_dict(self, invoice):
        """
        Prepares payment vals for invoice
        @author: Maulik Barad on Date 01-Dec-2022.
        """
        mollie = self.env.ref("payment.payment_provider_mollie")
        payment_method = mollie.mollie_methods_ids.filtered(
            lambda x: x.method_code == self.method
        )
        return {
            "journal_id": invoice.journal_id.id,
            "ref": self.payment_id,
            "currency_id": invoice.currency_id.id,
            "payment_type": "inbound",
            "date": invoice.date,
            "partner_id": invoice.partner_id.id,
            "amount": invoice.amount_residual,
            "payment_method_id": payment_method.id,
            "partner_type": "customer",
        }
