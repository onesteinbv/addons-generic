from odoo import fields, models


class MembershipGroupMember(models.Model):
    _name = "membership.group.member"
    _description = "Membership Group Member"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    group_id = fields.Many2one("membership.group", required=True, ondelete="cascade")
