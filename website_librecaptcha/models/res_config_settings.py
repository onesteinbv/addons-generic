from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_librecaptcha_enabled = fields.Boolean(
        string="Website LibreCaptcha",
        related="website_id.librecaptcha_enabled",
        readonly=False,
    )
    website_librecaptcha_level = fields.Selection(
        string="Website Level",
        related="website_id.librecaptcha_level",
        readonly=False,
    )
    website_librecaptcha_media = fields.Selection(
        string="Website Media",
        related="website_id.librecaptcha_media",
        readonly=False,
    )
    website_librecaptcha_type = fields.Selection(
        string="Website Type",
        related="website_id.librecaptcha_type",
        readonly=False,
    )
