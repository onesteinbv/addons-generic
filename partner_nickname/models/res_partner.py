from odoo import api, fields, models
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = "res.partner"

    nickname = fields.Char()

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        domain = expression.OR([domain, [("nickname", operator, value)]])
        return domain
