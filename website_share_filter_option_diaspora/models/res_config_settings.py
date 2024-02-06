from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_diaspora = fields.Boolean(
        related="website_id.share_diaspora", readonly=False
    )
