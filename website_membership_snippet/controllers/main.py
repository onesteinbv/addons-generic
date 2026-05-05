from odoo import http
from odoo.http import request


class MembershipSnippetController(http.Controller):
    @http.route("/membership/snippet/groups", type="json", auth="public", website=True)
    def snippet_groups(self):
        groups = (
            request.env["membership.group"]
            .sudo()
            .search(
                [
                    ("is_published", "=", True),
                ],
                order="name",
            )
        )
        return [{"id": g.id, "name": g.name} for g in groups]
