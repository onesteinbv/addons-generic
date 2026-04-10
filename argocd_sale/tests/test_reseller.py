from odoo import Command
from odoo.tests.common import TransactionCase


class TestReseller(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_pricelist = cls.env["product.pricelist"].create(
            [
                {
                    "name": "Test pricelist",
                }
            ]
        )
        cls.product = cls.env.ref(
            "argocd_sale.demo_product_basis_product_template"
        ).product_variant_ids[0].id

    def test_end_partner_is_invoiced(self):
        reseller = self.env["res.partner"].create(
            {"name": "Reseller", "is_reseller": True, "reselling_method": "customer"}
        )
        end_customer = self.env["res.partner"].create(
            {"name": "End Customer", "reseller_id": reseller.id}
        )
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": reseller.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.test_pricelist.id,
                "end_partner_id": end_customer.id,
                "sale_subscription_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product
                        }
                    )
                ],
            }
        )
        subscription.generate_invoice()
        invoice = subscription.invoice_ids[0]
        self.assertEqual(invoice.partner_id, end_customer)
        
    def test_reseller_is_invoiced(self):
        reseller = self.env["res.partner"].create(
            {"name": "Reseller", "is_reseller": True, "reselling_method": "reseller"}
        )
        end_customer = self.env["res.partner"].create(
            {"name": "End Customer", "reseller_id": reseller.id}
        )
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": reseller.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.test_pricelist.id,
                "end_partner_id": end_customer.id,
                "sale_subscription_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product
                        }
                    )
                ],
            }
        )
        subscription.generate_invoice()
        invoice = subscription.invoice_ids[0]
        self.assertEqual(invoice.partner_id, reseller)

    def test_no_end_partner(self):
        reseller = self.env["res.partner"].create(
            {"name": "Reseller", "is_reseller": True, "reselling_method": "customer"}
        )
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": reseller.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.test_pricelist.id,
                "sale_subscription_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product
                        }
                    )
                ],
            }
        )
        subscription.generate_invoice()
        invoice = subscription.invoice_ids[0]
        self.assertEqual(invoice.partner_id, reseller)
