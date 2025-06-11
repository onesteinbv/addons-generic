from odoo import fields, models


class MembershipActivityType(models.Model):
    _name = "membership.activity.type"
    _description = "Member Activity Type"

    name = fields.Char()
