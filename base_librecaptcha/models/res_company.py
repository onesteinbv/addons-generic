from odoo import fields, models


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
