from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_telegram = fields.Boolean(
        related="website_id.share_telegram", readonly=False
    )
