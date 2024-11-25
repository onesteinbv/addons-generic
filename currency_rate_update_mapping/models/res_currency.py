# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    res_currency_rate_provider_mapping_ids = fields.One2many(
        comodel_name="res.currency.rate.provider.mapping",
        inverse_name="currency_id",
        string="Currency Rate Provider Mappings",
        copy=False,
        help="Currency mapping with the rate provider for updating rates",
    )
