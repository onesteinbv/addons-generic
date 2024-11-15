from odoo import fields, models


class HRDepartment(models.Model):
    _inherit = "hr.department"

    membership_group_id = fields.Many2one("membership.group")
