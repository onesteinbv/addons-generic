from unittest.mock import patch

from odoo import Command, fields
from odoo.addons.account_payment.tests.common import AccountPaymentCommon


class TestSubscriptionPayment(AccountPaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.subscription_template = cls.env["sale.subscription.template"].create(
            {"name": "Website checkout test", "invoicing_mode": "draft"}
        )
        cls.subscription_pricelist = cls.env["product.pricelist"].create(
            {"name": "Website checkout test", "currency_id": cls.currency.id}
        )

    def _create_subscription(self):
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.subscription_template.id,
                "pricelist_id": self.subscription_pricelist.id,
                "sale_subscription_line_ids": [
                    Command.create(
                        {"product_id": self.product_a.id, "price_unit": 100.0}
                    )
                ],
            }
        )
        subscription.recurring_next_date = fields.Date.today()
        return subscription

    def _create_subscription_transaction(self, subscription, state):
        return self._create_transaction(
            "redirect",
            state=state,
            amount=subscription.amount_total,
            currency_id=subscription.currency_id.id,
            partner_id=subscription.partner_id.id,
            subscription_id=subscription.id,
        )

    def test_payment_link_values_do_not_create_invoice(self):
        subscription = self._create_subscription()

        values = subscription._get_default_payment_link_values()

        self.assertEqual(values["amount"], subscription.amount_total)
        self.assertEqual(values["currency_id"], subscription.currency_id.id)
        self.assertEqual(values["partner_id"], subscription.partner_id.id)
        self.assertFalse(subscription.invoice_ids)

    def test_payment_link_uses_subscription_id_and_standard_access_token(self):
        subscription = self._create_subscription()
        wizard = self.env["payment.link.wizard"].with_context(
            active_id=subscription.id, active_model=subscription._name
        ).create({})

        with patch(
            "odoo.addons.payment.utils.generate_access_token",
            return_value="access-token",
        ):
            params = wizard._prepare_query_params(subscription)

        self.assertEqual(params["subscription_id"], subscription.id)
        self.assertEqual(params["access_token"], "access-token")
        self.assertNotIn("subscription_access_token", params)
        self.assertNotIn("reference", params)

    def test_pending_payment_does_not_create_invoice(self):
        subscription = self._create_subscription()
        transaction = self._create_subscription_transaction(subscription, "pending")

        transaction._post_process()

        self.assertFalse(subscription.invoice_ids)
        self.assertFalse(transaction.payment_id)

    def test_failed_or_canceled_payment_does_not_create_invoice(self):
        for state in ("error", "cancel"):
            subscription = self._create_subscription()
            transaction = self._create_transaction(
                "redirect",
                state=state,
                reference=f"{self.reference}-{state}",
                amount=subscription.amount_total,
                currency_id=subscription.currency_id.id,
                partner_id=subscription.partner_id.id,
                subscription_id=subscription.id,
            )

            transaction._post_process()

            self.assertFalse(subscription.invoice_ids)
            self.assertFalse(transaction.payment_id)

    def test_confirmed_payment_creates_and_reconciles_invoice(self):
        subscription = self._create_subscription()
        transaction = self._create_subscription_transaction(subscription, "done")

        transaction._post_process()

        invoice = subscription.invoice_ids.ensure_one()
        self.assertEqual(transaction.invoice_ids, invoice)
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(transaction.payment_id.invoice_ids, invoice)
        self.assertEqual(transaction.payment_id.reconciled_invoice_ids, invoice)
        self.assertEqual(invoice.payment_state, "paid")

        transaction._post_process()
        self.assertEqual(subscription.invoice_ids, invoice)
