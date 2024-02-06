from odoo import fields, models


class MembershipActivity(models.Model):
    _inherit = "membership.activity"

    project_type_id = fields.Many2one(
        related="project_id.type_id", store=True, string="Project Type"
    )
