from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_mastodon = fields.Boolean(
        related="website_id.share_mastodon", readonly=False
    )
