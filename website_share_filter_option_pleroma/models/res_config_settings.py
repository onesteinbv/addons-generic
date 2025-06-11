from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_pleroma = fields.Boolean("")
    module_website_sale_share_pleroma = fields.Boolean("")
    website_share_pleroma = fields.Boolean(
        related="website_id.share_pleroma", readonly=False
    )
