from odoo import fields, models


class MembershipCommitteeMembership(models.Model):
    _name = "membership.committee.membership"
    _description = "Committee Membership"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    committee_id = fields.Many2one(
        "membership.committee", required=True, ondelete="cascade"
    )
