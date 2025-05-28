# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    name = fields.Char(size=6)
    rounding = fields.Float(digits=(12, 18))
