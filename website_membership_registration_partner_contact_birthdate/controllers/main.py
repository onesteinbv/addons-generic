import datetime

from odoo import _

from odoo.addons.website_membership_registration.controllers.main import (
    MembershipRegistrationController,
)


class MembershipRegistrationControllerBirthDate(MembershipRegistrationController):
    def _validate_membership_birthdate(self, birthdate):
        error_message, birthdate_valid = "", True
        if birthdate:
            try:
                birthdate = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
            except ValueError:
                birthdate_valid = False
                error_message = _("Birth Date is invalid.")
        return birthdate, birthdate_valid, error_message

    def _get_error_message_list(self, validation_data, error_data):
        error_list = super(
            MembershipRegistrationControllerBirthDate, self
        )._get_error_message_list(validation_data, error_data)
        if not validation_data["member_birthdate_date"]:
            error_list.append(error_data["member_birthdate_date"])
        return error_list

    def _get_partner_and_validation_data(self, post):
        partner_data, validation_data, error_data = super(
            MembershipRegistrationControllerBirthDate, self
        )._get_partner_and_validation_data(post)
        (
            partner_data["member_birthdate_date"],
            validation_data["member_birthdate_date"],
            error_data["member_birthdate_date"],
        ) = self._validate_membership_birthdate(post["member_birthdate_date"])
        return partner_data, validation_data, error_data

    def _get_new_member_vals_dict(self, partner_data):
        vals = super(
            MembershipRegistrationControllerBirthDate, self
        )._get_new_member_vals_dict(partner_data)
        if partner_data.get("member_birthdate_date"):
            vals["birthdate_date"] = partner_data["member_birthdate_date"]
        return vals
