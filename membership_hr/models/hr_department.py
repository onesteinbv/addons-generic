from odoo import fields, models


class HRDepartment(models.AbstractModel):
    _inherit = "hr.department"

    section_id = fields.Many2one("membership.section")
