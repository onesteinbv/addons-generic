# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).

from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("nl_rgs", "account.asset.group")
    def _get_nl_rgs_asset_group(self):
        return self._parse_csv(
            "nl_rgs", "account.asset.group", module="l10n_nl_rgs_asset"
        )

    @template("nl_rgs", "account.asset.profile")
    def _get_nl_rgs_asset_profile(self):
        return self._parse_csv(
            "nl_rgs", "account.asset.profile", module="l10n_nl_rgs_asset"
        )
