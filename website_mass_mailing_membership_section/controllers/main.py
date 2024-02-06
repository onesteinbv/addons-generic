from odoo import http
from odoo.http import request

from odoo.addons.website_membership_section.controllers import main


class MembershipSectionController(main.MembershipSectionController):
    def _section_page_render_vals(self, section):
        res = super()._section_page_render_vals(section)

        has_mailing_list = False
        in_mailing_list = False
        related_contact = False
        email_needed = False
        name_needed = False

        mailing_list = section.mailing_list_id
        if mailing_list:
            has_mailing_list = True

            if request.env.user._is_public():
                if request.session.get("section_%s_subscribed" % section.id, False):
                    in_mailing_list = True
                else:
                    email_needed = True
                    name_needed = True
            else:
                related_contacts = request.env.user.partner_id.mass_mailing_contact_ids
                if related_contacts:
                    related_contact = related_contacts[0]
                else:
                    if not request.env.user.partner_id.email:
                        email_needed = True

                related_lists = related_contacts.mapped("subscription_list_ids").mapped(
                    "list_id"
                )
                if mailing_list in related_lists:
                    in_mailing_list = True
                else:
                    in_mailing_list = False

        res.update(
            {
                "has_mailing_list": has_mailing_list,
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
        ["/subscribe-to-section-mailing-list"],
        type="http",
        methods=["POST"],
        auth="public",
        csrf=False,
        website=True,
    )
    def post_subscribe_to_section_mailing_list(self, **post):
        section_id = post.get("section_id")
        section = request.env["membership.section"].sudo().browse(int(section_id))

        if not section:
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

        section.mailing_list_id.write({"contact_ids": [(4, contact.id)]})

        request.session.update(
            {"section_%s_subscribed" % section.id: True, "related_contact": contact.id}
        )
        return request.redirect("/members/section/%s" % section.id)

    @http.route(
        ["/unsubscribe-from-section-mailing-list"],
        type="http",
        methods=["POST"],
        auth="public",
        csrf=False,
        website=True,
    )
    def post_unsubscribe_from_section_mailing_list(self, **post):
        section_id = post.get("section_id")
        section = request.env["membership.section"].sudo().browse(int(section_id))
        if not section:
            return http.request.not_found()

        if request.session.get("related_contact"):
            related_contacts = (
                request.env["mailing.contact"]
                .sudo()
                .browse(request.session.get("related_contact"))
            )
        else:
            partner = request.env.user.partner_id
            related_contacts = partner.mass_mailing_contact_ids

        section.mailing_list_id.write(
            {"contact_ids": [(3, contact.id) for contact in related_contacts]}
        )

        if request.session.get("section_%s_subscribed" % section.id):
            request.session.pop("section_%s_subscribed" % section.id)
        if request.session.get("related_contact"):
            request.session.pop("related_contact")
        return request.redirect("/members/section/%s" % section.id)
