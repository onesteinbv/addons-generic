from odoo.http import request

from odoo.addons.website_membership_registration.controllers.main import (
    MembershipRegistrationController,
)


class MembershipRegistrationControllerPrivacy(MembershipRegistrationController):
    def _get_partner_and_validation_data(self, post):
        partner_data, validation_data, error_data = super(
            MembershipRegistrationControllerPrivacy, self
        )._get_partner_and_validation_data(post)
        (
            partner_data["member_publish"],
            validation_data["member_publish"],
            error_data["member_publish"],
        ) = ("member_publish" in post and post["member_publish"] == "on", True, "")
        (
            partner_data["member_website_privacy"],
            validation_data["member_website_privacy"],
            error_data["member_website_privacy"],
        ) = (post["member_website_privacy"], True, "")
        return partner_data, validation_data, error_data

    def _get_new_member_vals_dict(self, partner_data):
        vals = super(
            MembershipRegistrationControllerPrivacy, self
        )._get_new_member_vals_dict(partner_data)
        vals["is_published"] = partner_data["member_publish"]
        vals["website_privacy"] = partner_data["member_website_privacy"]
        return vals

    def _get_membership_form_page_vals(
        self, is_logged, product, old_data=None, error_message="", errors=None
    ):
        vals = super(
            MembershipRegistrationControllerPrivacy, self
        )._get_membership_form_page_vals(
            is_logged,
            product,
            old_data=old_data,
            error_message=error_message,
            errors=errors,
        )
        vals.update(
            {
                "website_privacy_levels": request.env[
                    "res.partner"
                ].website_privacy_selection(),
                "member_website_privacy": request.env.company.default_website_privacy,
            }
        )
        return vals
