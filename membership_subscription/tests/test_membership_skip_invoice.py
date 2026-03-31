from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMembershipSkipInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "email": "test@example.com",
            }
        )

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "currency_id": cls.env.company.currency_id.id,
            }
        )

        cls.stage = cls.env.ref("subscription_oca.subscription_stage_in_progress")

        cls.subscription_template = cls.env["sale.subscription.template"].create(
            {
                "name": "Monthly Membership Template",
                "recurring_rule_type": "months",
                "recurring_interval": 1,
            }
        )

        cls.product_membership_skip = cls.env["product.product"].create(
            {
                "name": "Membership Product - Skip Invoice",
                "type": "service",
                "list_price": 0,
                "membership": True,
                "membership_skip_invoice": True,
                "subscribable": True,
                "subscription_template_id": cls.subscription_template.id,
            }
        )

        cls.product_membership_normal = cls.env["product.product"].create(
            {
                "name": "Membership Product - Normal",
                "type": "service",
                "list_price": 50.0,
                "membership": True,
                "membership_skip_invoice": False,
                "subscribable": True,
                "subscription_template_id": cls.subscription_template.id,
            }
        )

    def test_membership_skip_invoice_detection(self):
        """Test that _membership_skip_invoice correctly detects products with skip invoice flag"""
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": date.today(),
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_normal.id,
                "name": "Normal Membership",
                "price_unit": 50.0,
                "product_uom_qty": 1.0,
            }
        )

        self.assertFalse(subscription._membership_skip_invoice())

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 0,
                "product_uom_qty": 1.0,
            }
        )

        self.assertTrue(subscription._membership_skip_invoice())

    def test_generate_invoice_skip(self):
        """Test that generate_invoice skips invoice creation and creates membership lines instead"""
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": date.today(),
                "recurring_next_date": date.today(),
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 0,
                "product_uom_qty": 1.0,
            }
        )

        initial_invoice_count = self.env["account.move"].search_count(
            [("partner_id", "=", self.partner.id)]
        )
        initial_membership_count = self.env["membership.membership_line"].search_count(
            [("partner", "=", self.partner.id)]
        )

        subscription.generate_invoice()

        final_invoice_count = self.env["account.move"].search_count(
            [("partner_id", "=", self.partner.id)]
        )
        final_membership_count = self.env["membership.membership_line"].search_count(
            [("partner", "=", self.partner.id)]
        )

        self.assertEqual(initial_invoice_count, final_invoice_count)
        self.assertEqual(final_membership_count, initial_membership_count + 1)

        membership_line = self.env["membership.membership_line"].search(
            [("partner", "=", self.partner.id)], limit=1
        )
        self.assertEqual(membership_line.membership_id, self.product_membership_skip)
        self.assertEqual(membership_line.member_price, 0)
        self.assertEqual(membership_line.state, "free")

    def test_create_invoice_skip(self):
        """Test that create_invoice skips invoice creation for skip invoice products"""
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": date.today(),
                "recurring_next_date": date.today(),
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 0,
                "product_uom_qty": 1.0,
            }
        )

        initial_invoice_count = self.env["account.move"].search_count(
            [("partner_id", "=", self.partner.id)]
        )

        result = subscription.create_invoice()

        final_invoice_count = self.env["account.move"].search_count(
            [("partner_id", "=", self.partner.id)]
        )

        self.assertEqual(initial_invoice_count, final_invoice_count)
        self.assertFalse(result)

    def test_manual_invoice_skip(self):
        """Test that manual_invoice skips invoice creation for skip invoice products"""
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": date.today(),
                "recurring_next_date": date.today(),
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 0,
                "product_uom_qty": 1.0,
            }
        )

        initial_invoice_count = self.env["account.move"].search_count(
            [("partner_id", "=", self.partner.id)]
        )

        subscription.manual_invoice()

        final_invoice_count = self.env["account.move"].search_count(
            [("partner_id", "=", self.partner.id)]
        )

        self.assertEqual(initial_invoice_count, final_invoice_count)

    def test_membership_line_date_range(self):
        """Test that membership lines are created with correct date ranges"""
        start_date = date.today()
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": start_date,
                "recurring_next_date": start_date,
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 0,
                "product_uom_qty": 1.0,
            }
        )

        subscription.generate_invoice()

        membership_line = self.env["membership.membership_line"].search(
            [("partner", "=", self.partner.id)], limit=1
        )

        self.assertEqual(membership_line.date_from, start_date)
        expected_date_to = start_date + relativedelta(months=1)
        self.assertEqual(membership_line.date_to, expected_date_to)

    def test_mixed_products_invoice_behavior(self):
        """Test subscription with both skip invoice and normal products"""
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": date.today(),
                "recurring_next_date": date.today(),
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_normal.id,
                "name": "Normal Membership",
                "price_unit": 50.0,
                "product_uom_qty": 1.0,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 100.0,
                "product_uom_qty": 1.0,
            }
        )

        initial_membership_count = self.env["membership.membership_line"].search_count(
            [("partner", "=", self.partner.id)]
        )

        subscription.generate_invoice()

        final_membership_count = self.env["membership.membership_line"].search_count(
            [("partner", "=", self.partner.id)]
        )

        self.assertEqual(final_membership_count, initial_membership_count + 1)

        membership_line = self.env["membership.membership_line"].search(
            [("partner", "=", self.partner.id)], limit=1
        )
        self.assertEqual(membership_line.membership_id, self.product_membership_skip)

    def test_generate_subscription_date_range_with_skip_invoice(self):
        """Test _generate_subscription_date_range returns correct dates for skip invoice products"""
        start_date = date.today()
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": start_date,
                "recurring_next_date": start_date,
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 100.0,
                "product_uom_qty": 1.0,
            }
        )

        date_from, date_to = subscription._generate_subscription_date_range()

        self.assertEqual(date_from, start_date)
        expected_date_to = start_date + relativedelta(months=1)
        self.assertEqual(date_to, expected_date_to)

    def test_recurring_next_date_update(self):
        """Test that recurring_next_date is properly updated after generating membership lines"""
        start_date = date.today()
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": start_date,
                "recurring_next_date": start_date,
                "pricelist_id": self.pricelist.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "Skip Invoice Membership",
                "price_unit": 100.0,
                "product_uom_qty": 1.0,
            }
        )

        initial_next_date = subscription.recurring_next_date

        subscription.generate_invoice()

        self.assertNotEqual(subscription.recurring_next_date, initial_next_date)
        expected_next_date = start_date + relativedelta(months=1)
        self.assertEqual(subscription.recurring_next_date, expected_next_date)

    def test_multiple_skip_invoice_products(self):
        """Test subscription with multiple skip invoice products creates multiple membership lines"""
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "date_start": date.today(),
                "recurring_next_date": date.today(),
                "pricelist_id": self.pricelist.id,
            }
        )

        product_skip_2 = self.env["product.product"].create(
            {
                "name": "Second Skip Invoice Product",
                "type": "service",
                "list_price": 75.0,
                "membership": True,
                "membership_skip_invoice": True,
                "subscribable": True,
                "subscription_template_id": self.subscription_template.id,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": self.product_membership_skip.id,
                "name": "First Skip Invoice",
                "price_unit": 0,
                "product_uom_qty": 1.0,
            }
        )

        self.env["sale.subscription.line"].create(
            {
                "sale_subscription_id": subscription.id,
                "product_id": product_skip_2.id,
                "name": "Second Skip Invoice",
                "price_unit": 75.0,
                "product_uom_qty": 1.0,
            }
        )

        initial_membership_count = self.env["membership.membership_line"].search_count(
            [("partner", "=", self.partner.id)]
        )

        subscription.generate_invoice()

        final_membership_count = self.env["membership.membership_line"].search_count(
            [("partner", "=", self.partner.id)]
        )

        self.assertEqual(final_membership_count, initial_membership_count + 2)

        membership_lines = self.env["membership.membership_line"].search(
            [("partner", "=", self.partner.id)]
        )
        membership_products = membership_lines.mapped("membership_id")
        self.assertIn(self.product_membership_skip, membership_products)
        self.assertIn(product_skip_2, membership_products)
