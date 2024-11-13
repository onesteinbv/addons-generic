from odoo.addons.website_membership_registration.controllers.main import (
    MembershipRegistrationController,
)


class MembershipRegistrationControllerGithub(MembershipRegistrationController):
    def _get_partner_and_validation_data(self, post):
        partner_data, validation_data, error_data = super(
            MembershipRegistrationControllerGithub, self
        )._get_partner_and_validation_data(post)
        partner_data["member_birthdate_date"] = post.get("member_birthdate_date", "")
        return partner_data, validation_data, error_data

    def _get_new_member_vals_dict(self, partner_data):
        vals = super(
            MembershipRegistrationControllerGithub, self
        )._get_new_member_vals_dict(partner_data)
        if partner_data.get("member_github_login"):
            vals["github_login"] = partner_data["member_github_login"]
        if partner_data.get("member_gitlab_username"):
            vals["gitlab_username"] = partner_data["member_gitlab_username"]
        if partner_data.get("member_gitlab_email"):
            vals["gitlab_email"] = partner_data["member_gitlab_email"]
        return vals
