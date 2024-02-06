from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_tumblr = fields.Boolean(
        related="website_id.share_tumblr", readonly=False
    )
