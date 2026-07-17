from odoo import fields, models


class MembershipGroup(models.Model):
    _inherit = "membership.group"

    allow_registration = fields.Boolean(default=False)
