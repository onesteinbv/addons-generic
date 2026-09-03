import werkzeug

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
        ["""/members/group/<model("membership.group"):membership_group>"""],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def display_membership_group_page(self, membership_group):
        membership_group_sudo = membership_group.sudo()
        is_website_designer = request.env.user.has_group(
            "website.group_website_designer"
        )

        if not membership_group_sudo.is_published and not is_website_designer:
            raise werkzeug.exceptions.NotFound()

        if is_website_designer and not membership_group_sudo.page_id:
            page = membership_group_sudo._create_unique_website_page()
            return request.redirect(page.url)
        vals = self._membership_group_page_render_vals(membership_group_sudo)
        if membership_group_sudo.page_id:
            return request.render(membership_group_sudo.page_id.view_id.id, vals)
        return request.render("website_membership_group.membership_group_page", vals)
