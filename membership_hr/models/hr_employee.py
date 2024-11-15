from odoo import fields, models


class HREmployee(models.Model):
    _inherit = "hr.employee"

    membership_group_member_ids = fields.One2many(
        related="user_partner_id.membership_group_member_ids"
    )
