from odoo.tests import tagged

from odoo.addons.account_payment.tests.common import AccountPaymentCommon


@tagged("post_install", "-at_install")
class TestPaymentProviderMandateReuse(AccountPaymentCommon):
    def test_existing_mandate_reference_is_reused(self):
        mandate = self.env["payment.provider.mandate"].create(
            {
                "reference": "mollie-test-mandate",
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method_id,
            }
        )
        transaction = self._create_transaction("redirect")

        reused_mandate = transaction._create_payment_provider_mandate(mandate.reference)

        self.assertEqual(reused_mandate, mandate)
        self.assertEqual(
            self.env["payment.provider.mandate"].search_count(
                [("reference", "=", mandate.reference)]
            ),
            1,
        )

    def test_mandate_reference_insert_race_is_reused(self):
        mandate_model = self.env["payment.provider.mandate"]
        mandate = mandate_model.create(
            {
                "reference": "mollie-test-mandate-race",
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method_id,
            }
        )
        transaction = self._create_transaction("redirect")

        model_class = type(mandate_model)
        original_search = model_class.search
        search_calls = 0

        def search(model, domain, *args, **kwargs):
            nonlocal search_calls
            search_calls += 1
            if search_calls == 1:
                # Simulate another request inserting the reference after our lookup.
                return model.browse()
            return original_search(model, domain, *args, **kwargs)

        self.patch(model_class, "search", search)

        reused_mandate = transaction._create_payment_provider_mandate(mandate.reference)

        self.assertEqual(reused_mandate, mandate)
        self.assertGreaterEqual(search_calls, 2)
