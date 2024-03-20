from datetime import timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestGracePeriod(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestGracePeriod, cls).setUpClass()
        cls.sub_product_tmpl = cls.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        )
        cls.sub_product = cls.curq_product_tmpl.product_variant_ids[0]
        cls.sub_tmpl = cls.env.ref("argocd_sale.demo_subscription_template")
        cls.sub_tmpl = cls.env.ref("argocd_sale.demo_subscription_template")
        cls.disable_odoo_tag = cls.env["argocd.application.tag"].create(
            {"name": "Disable Odoo", "key": "disable_odoo", "is_odoo_module": True}
        )
        cls.partner_id = cls.env.ref("base.partner_admin")

        cls.grace_period = 90
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.grace_period", cls.grace_period
        )
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.grace_period_tag_id", cls.disable_odoo_tag.id
        )

    def _create_sub(self, last_date_invoiced):
        return self.env["sale.subscription"].create(
            {
                "template_id": self.sub_tmpl.id,
                "sale_subscription_line_ids": [
                    Command.create({"product_id": self.sub_product.id})
                ],
                "partner_id": self.partner_id.id,
                "pricelist_id": self.partner_id.property_product_pricelist.id,
                "last_date_invoiced": last_date_invoiced,
            }
        )

    def setUp(self):
        super(TestGracePeriod, self).setUp()
        today = fields.Date.today()
        late_date = today - timedelta(days=self.grace_period + 1)
        good_date = today - timedelta(days=1)
        self.draft_sub = self._create_sub(False)
        self.unpaid_sub = self._create_sub(late_date)
        self.paid_sub = self._create_sub(good_date)  # Paid yesterday

    def test_tag_action(self):
        self.env["ir.config_parameter"].set_param(
            "argocd_sale.grace_period_action", "add_tag"
        )
        self.env["sale.subscription"].cron_update_payment_provider_subscriptions()

        self.assertNotIn(
            self.disable_odoo_tag,
            self.draft_sub.mapped("application_ids.tag_ids"),
            "Draft subscription should be left alone",
        )
        self.assertIn(
            self.disable_odoo_tag, self.unpaid_sub.mapped("application_ids.tag_ids")
        )
        self.assertNotIn(
            self.disable_odoo_tag,
            self.paid_sub.mapped("application_ids.tag_ids"),
            "This subscription is paid yesterday it shouldn't be affected",
        )

    def test_destroy_action(self):
        pass
