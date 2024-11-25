# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from datetime import date, timedelta

from pycgapi import CoinGeckoAPI

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class ResCurrencyRateProviderCoinGecko(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("CoinGecko", "CoinGecko")],
        ondelete={"CoinGecko": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "CoinGecko":
            return super()._get_supported_currencies()
        # List of cryptocurrencies based on configured provider mappings
        supported_currencies = (
            self.env["res.currency.rate.provider.mapping"]
            .search([("provider_id", "=", self.id)])
            .mapped("currency_id.name")
        )
        return supported_currencies

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "CoinGecko":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        if date_from < date.today():
            return self._get_historical_rate_from_coingecko(
                date_from, date_to, base_currency
            )
        else:
            return self._get_latest_rate_from_coingecko(base_currency)

    def _get_latest_rate_from_coingecko(self, base_currency):
        """Get all the exchange rates for today"""
        api = CoinGeckoAPI()
        today = date.today()
        data = {today: {}}
        for (
            currency
        ) in self.currency_ids.res_currency_rate_provider_mapping_ids.filtered(
            lambda l: l.provider_id == self
        ):
            try:
                coin_data = api.coin_historical_on_date(
                    currency.provider_reference, today.strftime("%m-%d-%Y")
                )
            except Exception as e:
                _logger.warning(
                    'Currency Rate Provider "%(name)s" failed to obtain for %(currency)s currency'
                    % {
                        "name": self.name,
                        "currency": currency.currency_id.name,
                    },
                    exc_info=True,
                )
                self.message_post(
                    subject=_("Currency Rate Provider Failure"),
                    body=_(
                        'Currency Rate Provider "%(name)s" failed to obtain data(check the rate provider mapping on the currency) :\n%(error)s'
                    )
                    % {
                        "name": self.name,
                        "currency": currency.currency_id.name,
                        "error": str(e) if e else _("N/A"),
                    },
                )
                continue
            rate = (
                coin_data.get("market_data")
                .get("current_price")
                .get(base_currency.lower(), 0)
            )
            if rate:
                data[today].update({currency.currency_id.name: 1 / rate})
        return data

    def _get_historical_rate_from_coingecko(self, date_from, date_to, base_currency):
        """Get all the exchange rates from 'date_from' to 'date_to'"""
        api = CoinGeckoAPI()
        content = {}
        current_date = date_from
        while current_date <= date_to:
            content[current_date] = {}
            for (
                currency
            ) in self.currency_ids.res_currency_rate_provider_mapping_ids.filtered(
                lambda l: l.provider_id == self
            ):
                try:
                    coin_data = api.coin_historical_on_date(
                        currency.provider_reference, current_date.strftime("%m-%d-%Y")
                    )
                except Exception as e:
                    _logger.warning(
                        'Currency Rate Provider "%(name)s" failed to obtain for %(currency)s currency'
                        % {
                            "name": self.name,
                            "currency": currency.currency_id.name,
                        },
                        exc_info=True,
                    )
                    self.message_post(
                        subject=_("Currency Rate Provider Failure"),
                        body=_(
                            'Currency Rate Provider "%(name)s" failed to obtain data(check the rate provider mapping on the currency) :\n%(error)s'
                        )
                        % {
                            "name": self.name,
                            "currency": currency.currency_id.name,
                            "error": str(e) if e else _("N/A"),
                        },
                    )
                    continue
                rate = (
                    coin_data.get("market_data")
                    .get("current_price")
                    .get(base_currency.lower(), 0)
                )
                if rate:
                    content[current_date].update({currency.currency_id.name: 1 / rate})
            current_date += timedelta(days=1)
        return content
