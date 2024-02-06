from odoo.tests import common


class TestReseller(common.TransactionCase):
    def test_is_reseller(self):
        admin_partner = self.env.ref("base.partner_admin")
        demo_partner = self.env.ref("base.partner_demo")
        child_partner = self.env["res.partner"].create(
            {"name": "Sub Partner", "parent_id": admin_partner.id}
        )
        self.assertFalse(admin_partner.is_reseller)
        product_template = self.env["product.template"].create(
            {"name": "Reseller product", "reseller_partner_ids": admin_partner.ids}
        )
        self.assertTrue(admin_partner.is_reseller)

        app_by_reseller = self.env["argocd.application"].create(
            {
                "partner_id": admin_partner.id,
                "template_id": self.ref(
                    "argocd_deployer.demo_curq_basis_application_template"
                ),
                "name": "testtest",
            }
        )
        self.assertTrue(app_by_reseller.is_created_by_reseller())
        app_by_non_reseller = self.env["argocd.application"].create(
            {
                "partner_id": demo_partner.id,
                "template_id": self.ref(
                    "argocd_deployer.demo_curq_basis_application_template"
                ),
                "name": "testtest2",
            }
        )
        self.assertFalse(app_by_non_reseller.is_created_by_reseller())
        app_by_reseller_parent_partner = self.env["argocd.application"].create(
            {
                "partner_id": child_partner.id,
                "template_id": self.ref(
                    "argocd_deployer.demo_curq_basis_application_template"
                ),
                "name": "testtest3",
            }
        )
        self.assertTrue(app_by_reseller_parent_partner.is_created_by_reseller())

        product_template.unlink()
        self.assertFalse(admin_partner.is_reseller)
