from odoo import fields, models


class ResConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    website_privacy = fields.Selection(
        related="company_id.default_website_privacy",
        readonly=False,
    )
    show_email = fields.Boolean(
        related="company_id.default_show_email",
        readonly=False,
    )
    show_address = fields.Boolean(
        related="company_id.default_show_address",
        readonly=False,
    )
    show_phone = fields.Boolean(
        related="company_id.default_show_phone",
        readonly=False,
    )
    show_website = fields.Boolean(
        related="company_id.default_show_website",
        readonly=False,
    )
