import requests

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    librecaptcha_enabled = fields.Boolean()
    librecaptcha_url = fields.Char()
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
    librecaptcha_valid_server = fields.Boolean(
        compute="_compute_librecaptcha_valid_server",
        store=True,
    )

    @api.depends("librecaptcha_url")
    def _compute_librecaptcha_valid_server(self):
        for record in self:
            if not record.librecaptcha_url:
                record.librecaptcha_valid_server = False
                continue

            try:
                response = requests.get(record.librecaptcha_url, timeout=2)
                record.librecaptcha_valid_server = response.status_code == 200
            except requests.exceptions.ConnectionError:
                record.librecaptcha_valid_server = False

    @api.model
    def _cron_librecaptcha_check_server(self):
        self.search([])._compute_librecaptcha_valid_server()
