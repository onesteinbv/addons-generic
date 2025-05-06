from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
