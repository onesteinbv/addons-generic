from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_share_facebook = fields.Boolean(
        related="website_id.share_facebook", readonly=False
    )
    website_share_twitter = fields.Boolean(
        related="website_id.share_twitter", readonly=False
    )
    website_share_linkedin = fields.Boolean(
        related="website_id.share_linkedin", readonly=False
    )
    website_share_whatsapp = fields.Boolean(
        related="website_id.share_whatsapp", readonly=False
    )
    website_share_pinterest = fields.Boolean(
        related="website_id.share_pinterest", readonly=False
    )
    website_share_email = fields.Boolean(
        related="website_id.share_email", readonly=False
    )
