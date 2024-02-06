from odoo import api, fields, models


class MembershipSection(models.AbstractModel):
    _inherit = "membership.section"

    department_id = fields.Many2one(
        "hr.department",
        compute="_compute_department",
        inverse="_inverse_department",
        store=True,
        readonly=False,
    )

    department_ids = fields.One2many(
        "hr.department", "section_id", string="Departments"
    )

    @api.depends("department_ids")
    def _compute_department(self):
        for section in self:
            if len(self.department_ids) > 0:
                section.department_id = section.department_ids[0]
            else:
                section.department_id = False

    def _inverse_department(self):
        for section in self:
            if len(section.department_ids) > 0:
                department = self.env["hr.department"].browse(
                    section.department_ids[0].id
                )
                department.section_id = False
            section.department_id.section_id = section
