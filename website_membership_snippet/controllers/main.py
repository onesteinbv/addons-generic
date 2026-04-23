from odoo import http
from odoo.http import request


class MembershipSnippetController(http.Controller):
    @http.route("/membership/snippet/groups", type="json", auth="public", website=True)
    def snippet_groups(self):
        groups = request.env["membership.group"].sudo().search([
            ("is_published", "=", True),
        ], order="name")
        return [{"id": g.id, "name": g.name} for g in groups]

    @http.route("/membership/snippet/members", type="json", auth="public", website=True)
    def snippet_members(self, group_id=None):
        if not group_id:
            return []
        
        group = request.env["membership.group"].sudo().browse(int(group_id))
        if not group.exists():
            return []
        
        members = group.membership_group_member_ids.filtered(
            lambda m: m.state == "current"
        ).mapped("partner_id")
        
        result = []
        for member in members.filtered("website_published"):
            result.append({
                "id": member.id,
                "name": member.name,
                "description": member.website_description or "",
                "image": f"/web/image/res.partner/{member.id}/image_128" if member.image_128 else "",
                "url": f"/members/{request.env['ir.http']._slug(member)}" if member.website_published else "",
            })
        return result
