# Copyright 2023 Anjeel Haria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    visible_on_membership_registration_page = fields.Boolean(default=False)
