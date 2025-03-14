from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_anonymous = fields.Boolean(help="Hide visibility on group members page")
