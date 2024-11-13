from odoo import http
from odoo.http import request

from odoo.addons.website_membership_group.controllers import main


class MembershipGroupController(main.MembershipGroupController):
    def _membership_group_page_render_vals(self, membership_group):
        res = super()._membership_group_page_render_vals(membership_group)
        in_mailing_list, related_contact, email_needed, name_needed = (
            False,
            False,
            False,
            False,
        )
        mailing_list = membership_group.mailing_list_id
        if mailing_list:
            if request.env.user._is_public():
                if request.session.get(
                    "group_%s_subscribed" % membership_group.id, False
                ):
                    in_mailing_list = True
                else:
                    email_needed, name_needed = True, True
            else:
                related_contacts = request.env.user.partner_id.mass_mailing_contact_ids
                if related_contacts:
                    related_contact = related_contacts[0]
                else:
                    email_needed = bool(not request.env.user.partner_id.email)
                in_mailing_list = bool(
                    related_contacts.mapped("subscription_list_ids")
                    .mapped("list_id")
                    .filtered(lambda ml: ml == mailing_list)
                )
        res.update(
            {
                "mailing_list": mailing_list,
                "in_mailing_list": in_mailing_list,
                "related_contact": related_contact,
                "email_needed": email_needed,
                "name_needed": name_needed,
                "member_name": "",
                "member_email": "",
            }
        )
        return res

    def _get_contact_data(self, post, defaults=None):
        contact_data = {}
        if not defaults:
            defaults = {}
        contact_data["member_email"] = (
            defaults.get("member_email", "") or post["member_email"]
        )
        contact_data["member_name"] = (
            defaults.get("member_name", "") or post["member_name"]
        )
        return contact_data

    def _get_new_contact_vals_dict(self, partner_data):
        res = {
            "name": partner_data["member_name"],
            "email": partner_data["member_email"],
        }
        if not request.env.user._is_public() and request.env.user.partner_id:
            res["partner_id"] = request.env.user.partner_id.id
        return res

    @http.route(
        ["/subscribe-to-group-mailing-list"],
        type="http",
        methods=["POST"],
        auth="public",
        csrf=False,
        website=True,
    )
    def post_subscribe_to_membership_group_mailing_list(self, **post):
        group_id = post.get("group_id")
        group = request.env["membership.group"].sudo().browse(int(group_id))
        if not group:
            return http.request.not_found()
        if request.env.user._is_public():
            contact_data = self._get_contact_data(post)
            contact = (
                request.env["mailing.contact"]
                .sudo()
                .search(
                    [
                        ("email", "=", contact_data["member_email"]),
                        ("name", "=", contact_data["member_name"]),
                    ],
                    limit=1,
                )
            )
            if not contact:
                contact = (
                    request.env["mailing.contact"]
                    .sudo()
                    .create(self._get_new_contact_vals_dict(contact_data))
                )
        else:
            partner = request.env.user.partner_id
            related_contacts = partner.mass_mailing_contact_ids
            if related_contacts:
                contact = related_contacts[0]
            else:
                contact_data = self._get_contact_data(
                    post, {"member_name": partner.name, "member_email": partner.email}
                )
                contact = (
                    request.env["mailing.contact"]
                    .sudo()
                    .search(
                        [
                            ("email", "=", contact_data["member_email"]),
                            ("name", "=", contact_data["member_name"]),
                        ],
                        limit=1,
                    )
                )
                if not contact:
                    contact = (
                        request.env["mailing.contact"]
                        .sudo()
                        .create(self._get_new_contact_vals_dict(contact_data))
                    )
                else:
                    contact.write({"partner_id": partner.id})

        group.mailing_list_id.write({"contact_ids": [(4, contact.id)]})

        request.session.update(
            {"group_%s_subscribed" % group.id: True, "related_contact": contact.id}
        )
        return request.redirect("/members/group/%s" % group.id)

    @http.route(
        ["/unsubscribe-from-group-mailing-list"],
        type="http",
        methods=["POST"],
        auth="public",
        csrf=False,
        website=True,
    )
    def post_unsubscribe_from_membership_group_mailing_list(self, **post):
        group_id = post.get("group_id")
        group = request.env["membership.group"].sudo().browse(int(group_id))
        if not group:
            return http.request.not_found()

        if request.session.get("related_contact"):
            related_contacts = (
                request.env["mailing.contact"]
                .sudo()
                .browse(request.session.get("related_contact"))
            )
        else:
            related_contacts = request.env.user.partner_id.mass_mailing_contact_ids

        group.mailing_list_id.write(
            {"contact_ids": [(3, contact.id) for contact in related_contacts]}
        )
        request.session.pop("group_%s_subscribed" % group.id, None)
        request.session.pop("related_contact", None)
        return request.redirect("/members/group/%s" % group.id)
