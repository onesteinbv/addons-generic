from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    member_ids = fields.Many2many(
        "res.partner", string="Project Members", compute="_compute_member_ids"
    )

    @api.depends("assignment_ids")
    def _compute_member_ids(self):
        for project in self:
            project.member_ids = project.assignment_ids.mapped("user_id.partner_id")
