from odoo import fields, models


class MembershipGroupMember(models.Model):
    _name = "membership.group.member"
    _description = "Membership Group Member"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    group_id = fields.Many2one("membership.group", required=True, ondelete="cascade")
    wants_to_collaborate = fields.Boolean()
    type = fields.Selection(
        [
            ("follower", "Follower"),
            ("applicant", "Applicant"),
            ("applicant_follower", "Applicant / Follower"),
            ("collaborator_follower", "Collaborator / Follower"),
            ("collaborator", "Collaborator"),
            ("committee", "Committee"),
        ],
    )

    _sql_constraints = [
        (
            "partner_group_uniq",
            "unique(partner_id, group_id)",
            "Member already exists for this group!",
        )
    ]
