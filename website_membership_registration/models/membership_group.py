from odoo import api, fields, models


class MembershipGroup(models.Model):
    _inherit = "membership.group"

    follower_partner_count = fields.Integer(
        string="# of Following Members",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=True,
    )
    applicant_partner_count = fields.Integer(
        string="# of Applicant Members",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=True,
    )
    collaborator_partner_count = fields.Integer(
        string="# of Collaborating Members",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=True,
    )
    allow_registration = fields.Boolean(default=False)

    @api.depends(
        "membership_group_member_ids",
        "membership_group_member_ids.type",
    )
    def _compute_partner_ids(self):
        res = super(MembershipGroup, self)._compute_partner_ids()
        for membership_group in self:
            membership_group.follower_partner_count = len(
                membership_group.membership_group_member_ids.filtered(
                    lambda x: x.type
                    in ("follower", "applicant_follower", "collaborator_follower")
                ).mapped("partner_id")
            )
            membership_group.applicant_partner_count = len(
                membership_group.membership_group_member_ids.filtered(
                    lambda x: x.type in ("applicant", "applicant_follower")
                ).mapped("partner_id")
            )
            membership_group.collaborator_partner_count = len(
                membership_group.membership_group_member_ids.filtered(
                    lambda x: x.type in ("collaborator", "collaborator_follower")
                ).mapped("partner_id")
            )
        return res
