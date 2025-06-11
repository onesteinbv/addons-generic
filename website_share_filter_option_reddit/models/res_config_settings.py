from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_reddit = fields.Boolean("")
    module_website_sale_share_reddit = fields.Boolean("")
    website_share_reddit = fields.Boolean(
        related="website_id.share_reddit", readonly=False
    )
