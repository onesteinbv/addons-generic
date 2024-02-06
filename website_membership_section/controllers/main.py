from odoo import http
from odoo.http import request


class MembershipSectionController(http.Controller):
    def _section_page_render_vals(self, section):
        return {
            "main_object": section,
            "section": section,
            "title": section.name,
        }

    @http.route(
        [
            """/members/section/<model("membership.section","[('is_published', '=', True)]"):section>"""
        ],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
    )
    def display_section_page(self, section):
        section_sudo = section.sudo()
        is_website_designer = request.env["res.users"].has_group(
            "website.group_website_designer"
        )

        if not section_sudo.is_published and not is_website_designer:
            return request.not_found()

        if section_sudo.page_id:
            return request.redirect(section_sudo.page_id.url)

        vals = self._section_page_render_vals(section_sudo)

        return request.render("website_membership_section.section_page", vals)
