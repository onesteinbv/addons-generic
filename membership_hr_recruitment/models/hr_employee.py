from odoo import api, models


class HREmployee(models.Model):
    _inherit = "hr.employee"

    def get_member_groups(self):
        return self.env.ref("base.group_user").ids

    @api.model_create_multi
    def create(self, vals_list):
        employees = super(HREmployee, self).create(vals_list)
        to_update = employees.filtered(
            lambda e: e.employee_type == "member" and e.user_id
        )
        to_update.mapped("user_id").write(
            {"groups_id": [(6, 0, self.get_member_groups())]}
        )
        return employees
