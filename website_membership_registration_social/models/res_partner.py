from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    telegram = fields.Char("Telegram Link")
