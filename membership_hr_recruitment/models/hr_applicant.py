from odoo import fields, models


class HRApplicant(models.Model):
    _inherit = "hr.applicant"

    membership_applicant = fields.Boolean()
    section_membership_ids = fields.One2many(
        related="partner_id.section_membership_ids"
    )

    def create_employee_from_applicant(self):
        res = super(HRApplicant, self).create_employee_from_applicant()
        if self.membership_applicant:
            res["context"]["default_employee_type"] = "member"
            if self.partner_id.user_ids:
                res["context"]["default_user_id"] = self.partner_id.user_ids.ids[0]
        return res
