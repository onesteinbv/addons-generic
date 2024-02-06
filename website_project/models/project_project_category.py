from odoo import fields, models

from odoo.addons.http_routing.models.ir_http import slug


class ProjectProjectCategory(models.Model):
    _name = "project.project.category"
    _inherit = ["website.published.mixin"]
    _order = "sequence"
    _description = "Project Categories"

    name = fields.Char(required=True)
    description = fields.Text()
    sequence = fields.Integer()
    project_ids = fields.One2many("project.project", "category_id", string="Projects")

    def _compute_website_url(self):
        for project in self:
            project.website_url = "/projects/category/%s" % slug(project)
