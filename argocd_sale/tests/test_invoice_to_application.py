from odoo import Command, fields
from odoo.tests import common


class TestInvoiceToApplication(common.TransactionCase):
    def _create_subscription(self):
        partner = self.env["res.partner"].create({"name": "Onestein B.V. (some here)"})
        product = self.env.ref(
            "argocd_sale.demo_curq_basis_product_template"
        ).product_variant_ids

        # Change the default application set, because it's also the default
        application_set = self.env["argocd.application.set"].create(
            {
                "repository_url": "test",
                "repository_directory": "test",
                "name": "test-account-move-set",
                "branch": "test",
                "deployment_directory": "test",
                "template_id": self.env.ref(
                    "argocd_deployer.application_set_template_default"
                ).id,
                "domain_format": "1",
                "subdomain_format": "2",
            }
        )
        product.product_tmpl_id.application_set_id = application_set
        return self.env["sale.subscription"].create(
            {
                "partner_id": partner.id,
                "template_id": self.ref("argocd_sale.demo_subscription_template"),
                "pricelist_id": self.ref("product.list0"),
                "sale_subscription_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "price_unit": 1,
                        }
                    )
                ],
            }
        )

    def _create_posted_invoices(self, subscriptions):
        invoices = self.env["account.move"]
        for subscription in subscriptions:
            invoice = subscription.create_invoice()
            invoice.action_post()
            invoices |= invoice
        return invoices

    def _register_payments(self, invoices):
        for invoice in invoices:
            payment_method = self.env["account.payment.method.line"].search(
                [
                    ("journal_id.company_id", "=", invoice.company_id.id),
                    ("journal_id.type", "=", "bank"),
                    (
                        "payment_method_id",
                        "=",
                        self.ref("account.account_payment_method_manual_in"),
                    ),
                ]
            )
            register_payment = (
                self.env["account.payment.register"]
                .with_context(
                    {
                        "active_model": "account.move",
                        "active_id": invoice.id,
                        "active_ids": invoice.ids,
                    }
                )
                .create(
                    {
                        "payment_date": fields.Date.today(),
                        "journal_id": payment_method.journal_id.id,
                        "payment_method_line_id": payment_method.id,
                        "amount": invoice.amount_residual,
                    }
                )
            )
            register_payment.action_create_payments()
            self.assertEqual("paid", invoice.payment_state)

    def test_application_values(self):
        """Creating an application from an invoice populates it with the correct values."""
        subscription = self._create_subscription()
        product = subscription.sale_subscription_line_ids[0].product_id
        invoice = self._create_posted_invoices(subscription)
        self._register_payments(invoice)
        created_applications = self.env["argocd.application"].search(
            [("subscription_id", "in", subscription.ids)]
        )
        self.assertRecordValues(
            created_applications,
            [
                {
                    "name": "onestein-bv-some-here",
                    "template_id": product.application_template_id.id,
                    "tag_ids": product.application_tag_ids,
                    "application_set_id": product.application_set_id.id,
                }
            ],
        )

    def test_name_should_never_conflict(self):
        """Test if a customer can create multiple applications for themselves."""
        subscriptions = self._create_subscription()
        subscriptions |= subscriptions.copy()
        subscriptions[1].sale_subscription_line_ids = subscriptions[
            0
        ].sale_subscription_line_ids.copy()
        invoices = self._create_posted_invoices(subscriptions)
        self._register_payments(invoices)
        self.env["argocd.application"].flush_model()
        created_applications = self.env["argocd.application"].search(
            [("subscription_id", "in", subscriptions.ids)]
        )
        self.assertRecordValues(
            created_applications.sorted("id"),
            [
                {"name": "onestein-bv-some-here"},
                {"name": "onestein-bv-some-here0"},
            ],
        )

    def test_never_multiple_applications(self):
        pass  # TODO

    def test_application_tags(self):
        pass  # TODO
