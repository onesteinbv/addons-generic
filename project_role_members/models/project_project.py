from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    team_member_ids = fields.Many2many(
        "res.partner", string="Project Team Members", compute="_compute_team_member_ids"
    )
    manager_member_ids = fields.Many2many(
        "res.partner", string="Project Manager Members", compute="_compute_manager_member_ids"
    )

    @api.depends("assignment_ids", "assignment_ids.user_id", "assignment_ids.role_id",
                 "assignment_ids.role_id.is_manager","user_id")
    def _compute_team_member_ids(self):
        res_partner_obj = self.env["res.partner"]
        for project in self:
            project.team_member_ids = project.assignment_ids.filtered(lambda a: not a.role_id.is_manager).mapped(
                "user_id.partner_id") - (project.user_id and project.user_id.partner_id or res_partner_obj)

    @api.depends("assignment_ids", "assignment_ids.user_id", "assignment_ids.role_id",
                 "assignment_ids.role_id.is_manager","user_id")
    def _compute_manager_member_ids(self):
        res_partner_obj = self.env["res.partner"]
        for project in self:
            project.manager_member_ids = project.assignment_ids.filtered(lambda a: a.role_id.is_manager).mapped(
                "user_id.partner_id") - (project.user_id and project.user_id.partner_id or res_partner_obj)
