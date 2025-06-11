from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_skype = fields.Boolean("")
    module_website_sale_share_skype = fields.Boolean("")
    website_share_skype = fields.Boolean(
        related="website_id.share_skype", readonly=False
    )
