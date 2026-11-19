from contextlib import contextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from freezegun import freeze_time

from odoo.exceptions import ValidationError

from odoo.addons.argocd_website.controllers.payment import ArgocdPaymentPortal
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

    def _create_subscription(self, stage_type="initial_payment"):
        stage = self.env["sale.subscription.stage"].search(
            [("type", "=", stage_type)], limit=1
        )
        return self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "pricelist_id": self.partner.property_product_pricelist.id,
                "website_id": self.website.id,
                "stage_id": stage.id,
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

    def test_confirmed_payment_warning_clears_when_subscription_starts(self):
        subscription = self._create_subscription()
        transaction = self._create_application_transaction(subscription)
        transaction.state = "pending"
        self.assertFalse(subscription.has_confirmed_payment_not_in_progress)

        transaction.state = "done"
        self.assertTrue(subscription.has_confirmed_payment_not_in_progress)

        subscription.action_start_subscription()
        self.assertFalse(subscription.has_confirmed_payment_not_in_progress)

    def test_view_application_transactions_action_is_subscription_scoped(self):
        subscription = self._create_subscription()
        self._create_application_transaction(subscription)

        action = subscription.action_view_application_transactions()

        self.assertEqual(action["res_model"], "payment.transaction")
        self.assertEqual(action["view_mode"], "list,form")
        self.assertEqual(
            action["domain"],
            [("application_subscription_id", "=", subscription.id)],
        )

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

    def test_application_transaction_locks_subscription_before_creation(self):
        subscription = self._create_subscription(stage_type="draft")
        subscription.write(
            {
                "partner_id": self.env.user.partner_id.id,
                "user_id": self.env.user.id,
            }
        )
        controller = ArgocdPaymentPortal()
        transactions = []
        request_mock = SimpleNamespace(env=self.env, website=self.website)

        with (
            patch(
                "odoo.addons.argocd_website.controllers.payment.request",
                new=request_mock,
            ),
            patch("odoo.addons.payment.utils.check_access_token", return_value=True),
            patch.object(controller, "_create_transaction") as create_transaction,
            patch.object(controller, "_update_landing_route"),
            patch.object(
                self.env.registry["payment.transaction"],
                "_get_processing_values",
                return_value={},
            ),
        ):

            def create_transaction_after_lock(**kwargs):
                self.assertEqual(subscription.stage_id.type, "initial_payment")
                transaction = self._create_transaction(
                    flow=kwargs["flow"],
                    provider_id=kwargs["provider_id"],
                    payment_method_id=kwargs["payment_method_id"],
                    amount=kwargs["amount"],
                    currency_id=kwargs["currency_id"],
                    partner_id=kwargs["partner_id"],
                    application_subscription_id=kwargs["custom_create_values"][
                        "application_subscription_id"
                    ],
                    reference=f"Application {subscription.id}",
                )
                transactions.append(transaction)
                return transaction

            create_transaction.side_effect = create_transaction_after_lock
            controller.application_transaction(
                subscription.id,
                amount=subscription.amount_total,
                access_token="valid-token",
                provider_id=self.provider.id,
                payment_method_id=self.payment_method_id,
                token_id=None,
                flow="direct",
                tokenization_requested=False,
                landing_route="/payment/confirmation",
                is_validation=False,
                csrf_token="test-token",
            )
            with self.assertRaises(ValidationError):
                controller.application_transaction(
                    subscription.id,
                    amount=subscription.amount_total,
                    access_token="valid-token",
                    provider_id=self.provider.id,
                    payment_method_id=self.payment_method_id,
                    token_id=None,
                    flow="direct",
                    tokenization_requested=False,
                    landing_route="/payment/confirmation",
                    is_validation=False,
                    csrf_token="test-token",
                )

        create_transaction.assert_called_once()
        self.assertEqual(transactions[0].application_subscription_id, subscription)

    def test_application_transaction_rejects_stale_amount_before_locking(self):
        subscription = self._create_subscription(stage_type="draft")
        subscription.write(
            {
                "partner_id": self.env.user.partner_id.id,
                "user_id": self.env.user.id,
            }
        )
        controller = ArgocdPaymentPortal()
        request_mock = SimpleNamespace(env=self.env, website=self.website)

        with (
            patch(
                "odoo.addons.argocd_website.controllers.payment.request",
                new=request_mock,
            ),
            patch.object(controller, "_create_transaction") as create_transaction,
        ):
            with self.assertRaises(ValidationError):
                controller.application_transaction(
                    subscription.id,
                    amount=subscription.amount_total + 1,
                    access_token="invalid-token",
                )

        create_transaction.assert_not_called()
        self.assertEqual(subscription.stage_id.type, "draft")
