# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res["lang"] = "nl_NL"
        res["country_id"] = self.env.ref("base.nl").id
        return res
