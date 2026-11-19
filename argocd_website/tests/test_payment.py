from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from freezegun import freeze_time

from odoo.addons.payment.tests.common import PaymentCommon


class TestApplicationPayment(PaymentCommon):
    @contextmanager
    def mock_datetime_and_now(self, mock_dt):
        with freeze_time(mock_dt), patch.object(self.env.cr, "now", lambda: mock_dt):
            yield

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].search([], limit=1)
        cls.subscription_template = cls.env.ref(
            "argocd_sale.demo_subscription_template"
        )

    def _create_subscription(self):
        return self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "pricelist_id": self.partner.property_product_pricelist.id,
                "website_id": self.website.id,
                "stage_id": self.env.ref(
                    "argocd_website.subscription_stage_initial_payment"
                ).id,
            }
        )

    def _create_application_transaction(self, subscription):
        return self._create_transaction(
            flow="direct",
            application_subscription_id=subscription.id,
            reference=f"Application {subscription.id}",
        )

    def test_invoice_is_created_during_done_transaction_postprocessing(self):
        subscription = self._create_subscription()
        transaction = self._create_application_transaction(subscription)
        transaction.state = "done"
        sale_journal = self.env["account.journal"].search(
            [
                ("type", "=", "sale"),
                ("company_id", "=", subscription.company_id.id),
            ],
            limit=1,
        )

        def create_invoice(subscription_record):
            self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": subscription_record.partner_id.id,
                    "journal_id": sale_journal.id,
                    "subscription_id": subscription_record.id,
                }
            )

        with patch.object(
            self.env.registry["sale.subscription"],
            "generate_invoice",
            autospec=True,
            side_effect=create_invoice,
        ) as generate_invoice:
            transaction._post_process()

        generate_invoice.assert_called_once_with(subscription)
        self.assertEqual(transaction.invoice_ids, subscription.invoice_ids)

    def test_draft_transaction_does_not_create_invoice(self):
        subscription = self._create_subscription()
        transaction = self._create_application_transaction(subscription)

        with patch.object(
            self.env.registry["sale.subscription"],
            "generate_invoice",
            autospec=True,
        ) as generate_invoice:
            transaction._post_process()

        generate_invoice.assert_not_called()
        self.assertFalse(subscription.invoice_ids)

    def test_failed_transaction_keeps_subscription_locked_without_invoice(self):
        subscription = self._create_subscription()
        transaction = self._create_application_transaction(subscription)
        transaction.state = "error"

        transaction._post_process()

        self.assertEqual(subscription.stage_id.type, "initial_payment")
        self.assertFalse(subscription.invoice_ids)

    def test_abandoned_initial_payment_deletes_its_transaction(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "argocd_website.subscription_abandoned_period", "7"
        )
        with self.mock_datetime_and_now(datetime(2024, 1, 1, 10, 0, 0)):
            subscription = self._create_subscription()
            transaction = self._create_application_transaction(subscription)

        with self.mock_datetime_and_now(datetime(2024, 1, 9, 10, 0, 0)):
            self.env["sale.subscription"]._cron_cleanup_abandoned()

        self.assertFalse(subscription.exists())
        self.assertFalse(transaction.exists())
