from odoo import Command
from odoo.tests.common import TransactionCase


class TestSubscription(TransactionCase):
    def test_name_is_shortened(self):
        partner_with_long_name = self.env["res.partner"].create(
            {"name": "hello my company has a really long name"}  # 39 characters
        )
        prefix = "flavoured-odoo-prefix-"  # 22 characters
        product = self.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        ).product_variant_ids[0]
        # Make sure this still works if the demo data changes
        product.name = "curq"
        product.application_set_id.namespace_prefix_id.name = prefix
        sub = self.env["sale.subscription"].create(
            {
                "partner_id": partner_with_long_name.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.ref("product.list0"),
                "sale_subscription_line_ids": [
                    Command.create({"product_id": product.id})
                ],
            }
        )

        not_shortened_name = "hello-my-company-has-a-really-long-name-%s-%s" % (
            product.name,
            str(sub.sale_subscription_line_ids.id),
        )
        expected_removed_characters = len(not_shortened_name) + len(prefix) - 53
        shortened_name = not_shortened_name[expected_removed_characters:]
        if shortened_name[0] == "-":
            shortened_name = shortened_name[1:]
        actual_name = sub.sale_subscription_line_ids._to_application_name()
        self.assertNotEqual(actual_name[0], "-")
        self.assertEqual(len(actual_name), len(shortened_name))
        self.assertEqual(shortened_name, actual_name)
        self.assertLessEqual(len(actual_name), 53)

    def test_name_is_not_shortened(self):
        partner_with_long_name = self.env["res.partner"].create({"name": "short name"})
        prefix = "flavoured-odoo-prefix-"
        product = self.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        ).product_variant_ids[0]
        # Make sure this still works if the demo data changes
        product.name = "curq"
        product.application_set_id.namespace_prefix_id.name = prefix
        sub = self.env["sale.subscription"].create(
            {
                "partner_id": partner_with_long_name.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.ref("product.list0"),
                "sale_subscription_line_ids": [
                    Command.create({"product_id": product.id})
                ],
            }
        )
        actual_name = sub.sale_subscription_line_ids._to_application_name()
        expected_name = "short-name-%s-%s" % (
            product.name,
            str(sub.sale_subscription_line_ids.id),
        )
        self.assertEqual(actual_name, expected_name)

    def test_no_double_dash(self):
        partner_with_long_name = self.env["res.partner"].create(
            {"name": "james&&&&&&&&&&&&co"}
        )
        prefix = "flavoured-odoo-prefix-"
        product = self.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        ).product_variant_ids[0]
        # Make sure this still works if the demo data changes
        product.name = "curq"
        product.application_set_id.namespace_prefix_id.name = prefix
        sub = self.env["sale.subscription"].create(
            {
                "partner_id": partner_with_long_name.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.ref("product.list0"),
                "sale_subscription_line_ids": [
                    Command.create({"product_id": product.id})
                ],
            }
        )
        actual_name = sub.sale_subscription_line_ids._to_application_name()
        expected_name = "james-co-%s-%s" % (
            product.name,
            str(sub.sale_subscription_line_ids.id),
        )
        self.assertEqual(actual_name, expected_name)
