from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_tumblr = fields.Boolean("")
    module_website_sale_share_tumblr = fields.Boolean("")
    website_share_tumblr = fields.Boolean(
        related="website_id.share_tumblr", readonly=False
    )
