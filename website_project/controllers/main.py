from odoo import http
from odoo.http import request


class WebsiteProject(http.Controller):
    @http.route(["/projects"], type="http", auth="public", website=True, sitemap=True)
    def project_list(self, **kwargs):
        values = {
            "project_categories": request.env["project.project.category"]
            .sudo()
            .search([])
        }
        return request.render("website_project.project_project_list_template", values)

    @http.route(
        [
            """/projects/category/<model("project.project.category","[('is_published', '=', True)]"):category_id>"""
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def project_category(self, category_id, **kwargs):
        category_sudo = category_id.sudo()
        is_website_publisher = request.env["res.users"].has_group(
            "website.group_website_designer"
        )

        if not category_sudo.exists() or (
            not category_sudo.is_published and not is_website_publisher
        ):
            return request.redirect("/projects")

        vals = self._project_category_details_page_render_vals(category_sudo)
        return request.render("website_project.project_project_category_template", vals)

    def _project_category_details_page_render_vals(self, category):
        return {
            "main_object": category,
            "category": category,
            "title": category.name,
        }

    @http.route(
        [
            """/projects/<model("project.project","[('is_published', '=', True)]"):project_id>"""
        ],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
        sitemap=True,
    )
    def project_details(self, project_id, **kwargs):
        project_sudo = project_id.sudo()
        is_website_publisher = request.env["res.users"].has_group(
            "website.group_website_designer"
        )

        if not project_sudo.exists() or (
            not project_sudo.is_published and not is_website_publisher
        ):
            return request.redirect("/projects")

        vals = self._project_project_details_page_render_vals(project_sudo)
        return request.render("website_project.project_project_details_template", vals)

    def _project_project_details_page_render_vals(self, project):
        return {
            "main_object": project,
            "project": project,
            "title": project.name,
        }
