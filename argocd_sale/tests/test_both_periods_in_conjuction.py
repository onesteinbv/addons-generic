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
        cls.disable_odoo_tag = cls.env["argocd.application.tag"].create(
            {"name": "Disable Odoo", "key": "disable_odoo", "is_odoo_module": True}
        )
        cls.grace_period = 7
        cls.free_period = 14
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.grace_period", cls.grace_period
        )
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.grace_period_tag_id", cls.disable_odoo_tag.id
        )
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.grace_period_action", "add_tag"
        )
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.subscription_free_period", cls.free_period
        )
        cls.env["ir.config_parameter"].set_param(
            "argocd_sale.subscription_free_period_type", "days"
        )

    def test_in_trial(self):
        """Subs in trial shouldn't be affected by grace period"""
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
        sub._invoice_paid_hook()  # Trial end date should be today + 7 days
        sub.paid_for_date = fields.Date.today() - relativedelta(
            days=self.grace_period + 1
        )  # Make sure it's out of the grace period

        self.env["sale.subscription"].cron_update_payment_provider_subscriptions()
        self.assertNotIn(
            self.disable_odoo_tag,
            sub.mapped("application_ids.tag_ids"),
            "This sub is in the trial period and shouldn't be affected by grace period",
        )

    def test_just_out_of_trial(self):
        """Subs out of trial but not passed the grace period shouldn't be affected by grace period"""
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
        sub.free_trial_end_date = fields.Date.today() - relativedelta(
            days=2
        )  # Two days ago the free trial ended
        sub.paid_for_date = sub.free_trial_end_date - relativedelta(
            days=self.free_period
        )  # But no payment has been made yet (< grace period)
        # A payment must be made before trial period end + grace_period
        self.env["sale.subscription"].cron_update_payment_provider_subscriptions()
        self.assertNotIn(
            self.disable_odoo_tag,
            sub.mapped("application_ids.tag_ids"),
            "This sub is out of the trial period but grace period has not passed so shouldn't be affected by grace period",
        )

    def test_out_of_trial(self):
        """Subs out of trial and pass the grace period should be affected"""
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
        sub.free_trial_end_date = fields.Date.today() - relativedelta(
            days=self.grace_period + 1
        )  # Free trial ended
        sub.paid_for_date = sub.free_trial_end_date - relativedelta(
            days=self.free_period
        )  # To make it realistic the date the trial started
        self.env["sale.subscription"].cron_update_payment_provider_subscriptions()
        self.assertIn(self.disable_odoo_tag, sub.mapped("application_ids.tag_ids"))
