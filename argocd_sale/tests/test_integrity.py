from odoo.exceptions import ValidationError
from odoo.tests import common


class TestIntegrity(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.reseller = self.env.ref("base.res_partner_1")
        self.reseller_partner = self.env.ref("base.res_partner_12")
        self.non_reseller = self.env.ref("base.res_partner_2")
        self.some_partner = self.env.ref("base.res_partner_3")
        self.resellers_product = self.env.ref(
            "argocd_sale.demo_product_premium_product_template"
        )

    def test_non_reseller_cannot_have_reselling_products(self):
        """Only resellers should be able to have reselling products."""
        with self.assertRaises(
            ValidationError,
            msg="A non-reseller should not be able to have reselling products.",
        ):
            self.non_reseller.reselling_product_ids = [self.resellers_product.id]

    def test_non_reseller_cannot_have_reseller_partners(self):
        """Non-resellers should not be able to have reseller partners."""
        with self.assertRaises(
            ValidationError,
            msg="A non-reseller should not be able to have reseller partners.",
        ):
            self.non_reseller.reseller_partner_ids = [self.some_partner.id]

    def test_no_piramid_of_resellers(self):
        """A reseller should not be able to have another reseller as a parent."""
        with self.assertRaises(
            ValidationError,
            msg="A reseller should not be able to have another reseller as a parent.",
        ):
            self.env["res.partner"].create(
                {
                    "name": "Reseller child",
                    "is_reseller": True,
                    "parent_id": self.reseller.id,
                }
            )
        with self.assertRaises(
            ValidationError,
            msg="A reseller should not be able to have another reseller.",
        ):
            self.env["res.partner"].create(
                {
                    "name": "Reseller",
                    "is_reseller": True,
                    "reseller_id": self.reseller.id,
                }
            )

    def test_enforces_simple_parent_child_for_resellers(self):
        """Test wether the reseller can only have one layer of childs"""
        # First child partner should be created without issues.
        reseller_child = self.env["res.partner"].create(
            {
                "name": "Reseller child",
                "parent_id": self.reseller.id,
            }
        )
        with self.assertRaises(
            ValidationError,
            msg="A reseller child partner should not be able to have child partners.",
        ):
            reseller_child.child_ids = [self.some_partner.id]
