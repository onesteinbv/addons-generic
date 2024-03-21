from odoo import Command
from odoo.tests import common


class TestInvoiceToApplication(common.TransactionCase):
    def test_application_values(self):
        """Creating an application from an invoice populates it with the correct values."""
        partner = self.env["res.partner"].create({"name": "Onestein B.V. (some here)"})
        product = self.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        ).product_variant_ids

        # Change the default application set, because it's also the default
        application_set = self.env["argocd.application.set"].create(
            {
                "repository_url": "test",
                "repository_directory": "test",
                "name": "test_acocunt_move_set",
                "branch": "test",
                "instances_directory": "test",
                "domain_format": "1",
                "subdomain_format": "2",
            }
        )
        product.product_tmpl_id.application_set_id = application_set
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
        orders.action_confirm()
        invoices = orders._create_invoices(grouped=True)
        invoices.action_post()
        created_applications = self.env["argocd.application"].search(
            [("invoice_id", "in", invoices.ids)]
        )
        self.assertRecordValues(
            created_applications,
            [
                {
                    "name": "onestein-bv-some-here",
                    "template_id": product.application_template_id.id,
                    "tag_ids": product.application_tag_ids,
                    "application_set_id": application_set.id,
                }
            ],
        )

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
