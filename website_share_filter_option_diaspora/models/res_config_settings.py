from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_diaspora = fields.Boolean("")
    module_website_sale_share_diaspora = fields.Boolean("")
    website_share_diaspora = fields.Boolean(
        related="website_id.share_diaspora", readonly=False
    )
