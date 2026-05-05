import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


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
        sitemap=False,
    )
    def display_membership_group_page(self, membership_group):
        membership_group_sudo = membership_group.sudo()
        is_website_designer = request.env.user.has_group(
            "website.group_website_designer"
        )

        if not membership_group_sudo.is_published and not is_website_designer:
            return request.not_found()

        vals = self._membership_group_page_render_vals(membership_group_sudo)

        view_key = membership_group_sudo.page_id.view_id.key
        if not view_key:
            return request.not_found()

        try:
            return request.render(view_key, vals)
        except ValueError:
            return request.not_found()
        except Exception:
            _logger.exception(
                "Unexpected error rendering membership group page for view %s", view_key
            )
            return request.not_found()
