# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestResCurrencyRateProviderCoinGecko(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Company = cls.env["res.company"]
        cls.CurrencyRate = cls.env["res.currency.rate"]
        cls.Currency = cls.env["res.currency"]
        cls.CurrencyRateProvider = cls.env["res.currency.rate.provider"]
        cls.CurrencyRateProviderMapping = cls.env["res.currency.rate.provider.mapping"]

        cls.today = fields.Date.today()
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.company = cls.Company.create(
            {"name": "Test company", "currency_id": cls.eur_currency.id}
        )
        cls.lnk_currency = cls.Currency.create({"name": "LINK", "symbol": "LNK"})
        cls.coingecko_provider = cls.CurrencyRateProvider.search(
            [("service", "=", "CoinGecko")], limit=1
        )
        cls.coingecko_provider_mapping = cls.CurrencyRateProviderMapping.create(
            {
                "currency_id": cls.lnk_currency.id,
                "provider_id": cls.coingecko_provider.id,
                "provider_reference": "chainlink",
            }
        )
        cls.coingecko_provider.write(
            {
                "currency_ids": [
                    (4, cls.lnk_currency.id),
                ],
            }
        )
        cls.env.user.company_ids += cls.company
        cls.env.company = cls.company
        cls.CurrencyRate.search([]).unlink()

    def test_supported_currencies_CoinGecko(self):
        self.coingecko_provider._get_supported_currencies()

    def test_cron(self):
        self.coingecko_provider._scheduled_update()
        rates = self.CurrencyRate.search([])
        self.assertTrue(rates)
        self.assertEqual(rates.currency_id, self.lnk_currency)
        self.CurrencyRate.search([("company_id", "=", self.company.id)]).unlink()

    def test_wizard(self):
        wizard = (
            self.env["res.currency.rate.update.wizard"]
            .with_context(
                default_provider_ids=[(6, False, self.coingecko_provider.ids)]
            )
            .create({})
        )
        wizard.action_update()
        rates = self.CurrencyRate.search([])
        self.assertTrue(rates)
        self.assertEqual(rates.currency_id, self.lnk_currency)
        self.CurrencyRate.search([("company_id", "=", self.company.id)]).unlink()

    @mute_logger(
        "odoo.addons.currency_rate_update_coingecko.models.res_currency_rate_provider_CoinGecko"
    )
    def test_error_CoinGecko(self):
        self.coingecko_provider_mapping.write({"provider_reference": "test"})
        self.coingecko_provider._update(self.today, self.today)
        rates = self.CurrencyRate.search([])
        self.assertEqual(len(rates), 0)
        self.coingecko_provider._update(self.today - relativedelta(days=2), self.today)
        rates = self.CurrencyRate.search([])
        self.assertEqual(len(rates), 0)
