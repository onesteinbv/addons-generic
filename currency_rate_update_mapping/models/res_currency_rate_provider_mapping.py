# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCurrencyRateProviderMapping(models.Model):
    _name = "res.currency.rate.provider.mapping"
    _description = "Currency Rate Provider Mapping"

    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
    )
    provider_id = fields.Many2one(
        string="Provider",
        comodel_name="res.currency.rate.provider",
        ondelete="restrict",
    )
    provider_reference = fields.Char(
        required=True,
        help="Defines the reference to be used when fetching rates from the provider",
    )
