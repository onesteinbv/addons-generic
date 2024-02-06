from odoo import api, fields, models

from odoo.addons.http_routing.models.ir_http import slug


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "image.mixin", "website.published.mixin"]

    short_description = fields.Text()
    description = fields.Html()
    category_id = fields.Many2one(
        comodel_name="project.project.category", string="Category"
    )
    slug = fields.Char(compute="_compute_slug", store=True)

    @api.depends("display_name")
    def _compute_slug(self):
        for project in self:
            project.slug = slug(project)

    def _compute_website_url(self):
        for project in self:
            project.website_url = "/projects/%s" % project.slug

    def _get_placeholder_filename(self, field):
        image_fields = ["image_%s" % size for size in [1920, 1024, 512, 256, 128]]
        if field in image_fields:
            return "project/static/description/icon.png"
        return super()._get_placeholder_filename(field)
