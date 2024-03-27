from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestFreePeriod(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestFreePeriod, cls).setUpClass()
        cls.sub_product_tmpl = cls.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        )
        cls.sub_product = cls.sub_product_tmpl.product_variant_ids[0]
        cls.sub_tmpl = cls.env.ref("argocd_sale.demo_subscription_template")
        cls.partner_id = cls.env.ref("base.partner_admin")
        cls.sub_product.list_price = 30.0  # Make sure it's not 1.0

    def test_disabled(self):
        self.env["ir.config_parameter"].set_param(
            "argocd_sale.subscription_free_period", 3
        )
        self.env["ir.config_parameter"].set_param(
            "argocd_sale.subscription_free_period_type", ""  # This should disable it.
        )
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
        sub.generate_invoice()
        sub._invoice_paid_hook()
        self.assertEqual(
            sub.invoice_ids.amount_untaxed,
            30.0,
            "Free period should be disabled",
        )

    def test_next_payment_date_and_price(self):
        self.env["ir.config_parameter"].set_param(
            "argocd_sale.subscription_free_period", 3
        )
        self.env["ir.config_parameter"].set_param(
            "argocd_sale.subscription_free_period_type", "months"
        )
        expected_next_payment_date = fields.Date.today() + relativedelta(months=3)
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
        sub.generate_invoice()
        sub._invoice_paid_hook()
        self.assertEqual(sub.recurring_next_date, expected_next_payment_date)
        self.assertEqual(
            sub.invoice_ids.amount_untaxed,
            1.0,
            "Invoice amount of first invoice must be 1.0",
        )

        sub.generate_invoice()
        sub._invoice_paid_hook()
        self.assertEqual(
            sub.invoice_ids[0].amount_untaxed,  # It's order newest to oldest
            30.0,
            "Next invoice should be the normal price",
        )

        sub2 = self.env["sale.subscription"].create(
            {
                "template_id": self.sub_tmpl.id,
                "sale_subscription_line_ids": [
                    Command.create({"product_id": self.sub_product.id})
                ],
                "partner_id": self.partner_id.id,
                "pricelist_id": self.partner_id.property_product_pricelist.id,
            }
        )
        sub2.generate_invoice()
        sub2._invoice_paid_hook()
        self.assertEqual(
            sub2.invoice_ids.amount_untaxed,
            30.0,
            "Invoice of new second subscription must be the normal price",
        )
