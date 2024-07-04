from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestFields(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestFields, cls).setUpClass()
        cls.sub_product = cls.env.ref("product.product_product_12")
        cls.sub_tmpl = cls.env["sale.subscription.template"].create(
            {
                "recurring_interval": 7,
                "recurring_rule_type": "days",
                "invoicing_mode": "invoice_send",
                "name": "Weekly",
            }
        )
        cls.partner_id = cls.env.ref("base.partner_admin")

    def test_paid_for_date(self):
        sub = self.env["sale.subscription"].create(
            {
                "template_id": self.sub_tmpl.id,
                "sale_subscription_line_ids": [
                    Command.create({"product_id": self.sub_product.id})
                ],
                "partner_id": self.partner_id.id,
                "pricelist_id": self.partner_id.property_product_pricelist.id,
            }
        )
        today = fields.Date.today()
        sub.generate_invoice()
        sub.generate_invoice()
        sub.generate_invoice()

        invoices = sub.invoice_ids.sorted("invoice_date")
        self.assertEqual(invoices[0].invoice_date, today)
        self.assertEqual(invoices[1].invoice_date, today + relativedelta(days=7))
        self.assertEqual(invoices[2].invoice_date, today + relativedelta(days=14))
        self.assertFalse(sub.paid_for_date)

        # Needs sale_recurring_payment_mollie e.g. installed to work, we can't do this here
        # self.env["payment.transaction"]._process_payment_provider_mandate_recurring_payment(
        #     sub
        # )

        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoices[0].ids
        ).create({}).action_create_payments()
        self.assertEqual(sub.paid_for_date, today + relativedelta(days=7))
