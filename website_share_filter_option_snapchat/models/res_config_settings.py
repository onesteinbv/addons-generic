from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_snapchat = fields.Boolean(
        related="website_id.share_snapchat", readonly=False
    )
