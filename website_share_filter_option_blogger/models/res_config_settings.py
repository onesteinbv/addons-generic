from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_blogger = fields.Boolean("")
    module_website_sale_share_blogger = fields.Boolean("")
    website_share_blogger = fields.Boolean(
        related="website_id.share_blogger", readonly=False
    )
