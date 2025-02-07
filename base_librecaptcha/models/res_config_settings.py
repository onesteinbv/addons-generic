from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    librecaptcha_enabled = fields.Boolean(
        related="company_id.librecaptcha_enabled",
        readonly=False,
    )
    librecaptcha_url = fields.Char(
        related="company_id.librecaptcha_url",
        readonly=False,
    )
    librecaptcha_level = fields.Selection(
        related="company_id.librecaptcha_level",
        readonly=False,
    )
    librecaptcha_media = fields.Selection(
        related="company_id.librecaptcha_media",
        readonly=False,
    )
    librecaptcha_type = fields.Selection(
        related="company_id.librecaptcha_type",
        readonly=False,
    )
