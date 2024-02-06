from odoo.tests import common


class TestSecurity(common.TransactionCase):
    def test_product_access(self):
        reseller = self.env.ref("base.template_portal_user_id").copy(
            {"login": "reseller", "name": "Reseller Account", "active": True}
        )
        not_reseller = self.env.ref("base.template_portal_user_id").copy(
            {"login": "not_reseller", "name": "Not a Reseller", "active": True}
        )
        variant_ids = (
            self.env["product.template"]
            .create(
                {
                    "name": "Reseller product",
                    "reseller_partner_ids": reseller.partner_id.ids,
                    "application_template_id": self.ref(
                        "argocd_deployer.demo_curq_basis_application_template"
                    ),
                }
            )
            .mapped("product_variant_id")
            .ids
        )  # Test with product.product

        with self.with_user(reseller.login):
            self.assertEqual(
                self.env["product.product"].search(
                    [("id", "in", variant_ids)], count=True
                ),
                len(variant_ids),
                "Reseller should have access to the product",
            )

        with self.with_user(not_reseller.login):
            self.assertEqual(
                self.env["product.product"].search(
                    [("id", "in", variant_ids)], count=True
                ),
                0,
                "Non-reseller should not have access to this product",
            )
