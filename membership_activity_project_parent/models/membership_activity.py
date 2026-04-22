from odoo import fields, models


class MembershipActivity(models.Model):
    _inherit = "membership.activity"

    parent_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Parent Project",
        related="project_id.parent_id",
        store=True,
        index=True,
    )
