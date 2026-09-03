from odoo import fields, models


class MembershipGroupMemberType(models.Model):
    _name = "membership.group.member.type"
    _description = "Membership Group Member Type"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    group_ids = fields.Many2many(
        comodel_name="membership.group",
        string="Allowed Groups",
        help="If kept empty, it is available for all groups.",
    )
