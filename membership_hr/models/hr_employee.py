from odoo import fields, models


class HREmployee(models.AbstractModel):
    _inherit = "hr.employee"

    section_membership_ids = fields.One2many(
        related="user_partner_id.section_membership_ids"
    )
