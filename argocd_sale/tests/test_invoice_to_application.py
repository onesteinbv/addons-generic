from odoo import Command
from odoo.tests import common


class TestInvoiceToApplication(common.TransactionCase):
    def test_name_should_never_conflict(self):
        """Test if a customer can create multiple applications for themselves."""
        partner = self.env["res.partner"].create({"name": "Onestein B.V. (some here)"})
        product = self.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        ).product_variant_ids
        orders = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    Command.create(
                        {"name": "Product", "product_id": product.id, "price_unit": 0}
                    )
                ],
            }
        )
        orders += orders.copy()
        orders.action_confirm()
        invoices = orders._create_invoices(grouped=True)
        invoices.action_post()
        created_applications = self.env["argocd.application"].search(
            [("invoice_id", "in", invoices.ids)]
        )
        application_names = created_applications.mapped("name")
        self.assertEqual(len(created_applications), 2)
        self.assertIn("onestein-bv-some-here", application_names)
        self.assertIn("onestein-bv-some-here0", application_names)

    def test_never_multiple_applications(self):
        pass  # TODO

    def test_application_tags(self):
        pass  # TODO
