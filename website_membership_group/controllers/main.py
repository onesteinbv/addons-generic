from odoo import http
from odoo.http import request


class MembershipGroupController(http.Controller):
    def _membership_group_page_render_vals(self, membership_group):
        return {
            "main_object": membership_group,
            "membership_group": membership_group,
            "title": membership_group.name,
        }

    @http.route(
        [
            """/members/group/<model("membership.group","[('is_published', '=', True)]"):membership_group>"""
        ],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
    )
    def display_membership_group_page(self, membership_group):
        membership_group_sudo = membership_group.sudo()
        is_website_designer = request.env["res.users"].has_group(
            "website.group_website_designer"
        )

        if not membership_group_sudo.is_published and not is_website_designer:
            return request.not_found()

        if membership_group_sudo.page_id:
            return request.redirect(membership_group_sudo.page_id.url)

        vals = self._membership_group_page_render_vals(membership_group_sudo)

        return request.render("website_membership_group.membership_group_page", vals)
