from odoo import fields, models


class ProjectProjectCategory(models.Model):
    _name = "project.project.category"
    _inherit = ["website.published.mixin", "website.seo.metadata"]
    _order = "sequence"
    _description = "Project Categories"

    name = fields.Char(required=True)
    description = fields.Text()
    sequence = fields.Integer()
    project_ids = fields.One2many("project.project", "category_id", string="Projects")

    def _compute_website_url(self):
        slug = self.env["ir.http"]._slug
        for project in self:
            project.website_url = "/projects/category/%s" % slug(project)
