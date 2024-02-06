from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_reddit = fields.Boolean(
        related="website_id.share_reddit", readonly=False
    )
