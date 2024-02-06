from odoo import fields, models


class HREmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    employee_type = fields.Selection(
        selection_add=[("member", "Member")], ondelete={"member": "set default"}
    )
