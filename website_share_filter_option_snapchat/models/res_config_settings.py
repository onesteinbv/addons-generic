from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_snapchat = fields.Boolean("")
    module_website_sale_share_snapchat = fields.Boolean("")
    website_share_snapchat = fields.Boolean(
        related="website_id.share_snapchat", readonly=False
    )
