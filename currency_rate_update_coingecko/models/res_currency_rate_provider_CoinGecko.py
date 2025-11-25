# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from datetime import timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from odoo import _, fields, models

_logger = logging.getLogger(__name__)
API_URL = "https://api.coingecko.com/api/v3/coins/%s/history"
PRO_API_URL = "https://pro-api.coingecko.com/api/v3/coins/%s/history"


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
            .search([("provider_service", "=", self.service)])
            .mapped("currency_id.name")
        )
        return supported_currencies

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "CoinGecko":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        return self._get_historical_rate_from_coingecko(
            date_from, date_to, base_currency
        )

    def _get_historical_rate_from_coingecko(self, date_from, date_to, base_currency):
        """Get all the exchange rates from 'date_from' to 'date_to'"""
        content = {}
        current_date = date_from
        api_key = self.env["ir.config_parameter"].get_param("X-CG_PRO_API_KEY")
        while current_date <= date_to:
            content[current_date] = {}
            for (
                currency
            ) in self.currency_ids.res_currency_rate_provider_mapping_ids.filtered(
                lambda rpm: rpm.provider_service == self.service
            ):
                try:
                    coin_data = self._get_coin_data_for_date(
                        currency.provider_reference, current_date, api_key
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
                if coin_data:
                    rate = (
                        coin_data.get("market_data", {})
                        .get("current_price", {})
                        .get(base_currency.lower(), 0)
                    )
                    if rate:
                        content[current_date].update(
                            {currency.currency_id.name: 1 / rate}
                        )
            current_date += timedelta(days=1)
        return content

    def _get_coin_data_for_date(self, provider_reference, current_date, api_key):
        """Get the exchange rate for a coin on the given date"""
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount("https://", adapter)
        params = {"date": current_date.strftime("%d-%m-%Y"), "localization": "en"}
        if api_key:
            response = session.get(
                PRO_API_URL % provider_reference,
                params=params,
                headers={"x-cg-pro-api-key": api_key},
            )
        else:
            response = session.get(API_URL % provider_reference, params=params)
        response.raise_for_status()
        return response.json()
