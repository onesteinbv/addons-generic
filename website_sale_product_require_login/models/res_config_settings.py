from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_sale_product_require_login = fields.Boolean(
        related="website_id.website_sale_product_require_login", readonly=False
    )
