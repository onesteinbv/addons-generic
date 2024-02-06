from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    website_sale_product_require_login = fields.Boolean(
        string="Require login to use webshop"
    )
