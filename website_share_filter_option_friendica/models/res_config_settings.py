from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_friendica = fields.Boolean(
        related="website_id.share_friendica", readonly=False
    )
