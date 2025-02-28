from odoo import api, fields, models


class Website(models.Model):
    _inherit = "website"

    company_librecaptcha_enabled = fields.Boolean(
        string="Company LibreCaptcha Enabled",
        related="company_id.librecaptcha_enabled",
        store=True,
    )
    librecaptcha_enabled = fields.Boolean(
        compute="_compute_librecaptcha_enabled",
        store=True,
        readonly=False,
    )
    librecaptcha_url = fields.Char(related="company_id.librecaptcha_url")
    librecaptcha_valid_server = fields.Boolean(
        related="company_id.librecaptcha_valid_server"
    )

    librecaptcha_level = fields.Selection(
        [
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
        ],
        default="hard",
        required=True,
    )
    librecaptcha_media = fields.Selection(
        [
            ("png", "PNG"),
            ("gif", "GIF"),
        ],
        default="png",
        required=True,
    )
    librecaptcha_type = fields.Selection(
        [
            ("text", "Text"),
        ],
        default="text",
        required=True,
    )

    @api.depends("company_librecaptcha_enabled")
    def _compute_librecaptcha_enabled(self):
        for record in self:
            if not record.company_librecaptcha_enabled:
                record.librecaptcha_enabled = False
