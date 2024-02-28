from odoo import api, fields, models


class MembershipSection(models.Model):
    _inherit = "membership.section"

    follower_partner_count = fields.Integer(
        string="# of Following Members",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=False,
    )
    applicant_partner_count = fields.Integer(
        string="# of Applicant Members",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=False,
    )
    collaborator_partner_count = fields.Integer(
        string="# of Collaborating Members",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=False,
    )

    @api.depends(
        "section_membership_ids",
        "section_membership_ids.on_mailing_list",
        "section_membership_ids.wants_to_collaborate",
        "section_membership_ids.partner_id",
        "section_membership_ids.partner_id.employee_ids",
        "section_membership_ids.partner_id.applicant_ids",
    )
    def _compute_partner_ids(self):
        res = super(MembershipSection, self)._compute_partner_ids()
        for section in self:
            section.follower_partner_count = len(
                section.section_membership_ids.filtered(
                    lambda x: x.on_mailing_list
                ).mapped("partner_id")
            )
            section.applicant_partner_count = len(
                section.section_membership_ids.filtered(
                    lambda x: x.type == "applicant"
                ).mapped("partner_id")
            )
            section.collaborator_partner_count = len(
                section.section_membership_ids.filtered(
                    lambda x: x.type == "collaborator"
                ).mapped("partner_id")
            )
        return res
