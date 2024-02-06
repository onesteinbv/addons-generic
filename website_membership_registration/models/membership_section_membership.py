from odoo import api, fields, models


class MembershipSectionMembership(models.Model):
    _inherit = "membership.section.membership"

    wants_to_collaborate = fields.Boolean()
    type = fields.Selection(
        [
            ("follower", "Follower"),
            ("applicant", "Applicant"),
            ("applicant_follower", "Applicant / Follower"),
            ("collaborator_follower", "Collaborator / Follower"),
            ("collaborator", "Collaborator"),
        ],
        compute="_compute_type",
        store=True,
    )

    @api.depends(
        "partner_id",
        "on_mailing_list",
        "wants_to_collaborate",
        "partner_id.employee_ids",
        "partner_id.applicant_ids",
    )
    def _compute_type(self):
        for membership in self:
            if membership.on_mailing_list:
                if membership.wants_to_collaborate:
                    if membership.partner_id.employee_ids:
                        membership.type = "collaborator_follower"
                    elif membership.partner_id.applicant_ids:
                        membership.type = "applicant_follower"
                    else:
                        membership.type = "collaborator_follower"
                else:
                    membership.type = "follower"
            else:
                if membership.wants_to_collaborate:
                    if membership.partner_id.employee_ids:
                        membership.type = "collaborator"
                    elif membership.partner_id.applicant_ids:
                        membership.type = "follower"
                    else:
                        membership.type = "collaborator"
                else:
                    membership.type = None
