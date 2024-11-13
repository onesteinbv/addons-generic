from odoo import api, fields, models


class MembershipGroup(models.AbstractModel):
    _inherit = "membership.group"

    department_id = fields.Many2one(
        "hr.department",
        compute="_compute_department",
        inverse="_inverse_department",
        store=True,
        readonly=False,
    )

    department_ids = fields.One2many(
        "hr.department", "membership_group_id", string="Departments"
    )

    @api.depends("department_ids")
    def _compute_department(self):
        for membership_group in self:
            membership_group.department_id = (
                membership_group.department_ids
                and membership_group.department_ids[0]
                or False
            )

    def _inverse_department(self):
        hr_department_obj = self.env["hr.department"]
        for membership_group in self:
            if membership_group.department_ids:
                department = hr_department_obj.browse(
                    membership_group.department_ids[0].id
                )
                department.membership_group_id = False
            membership_group.department_id.membership_group_id = membership_group
