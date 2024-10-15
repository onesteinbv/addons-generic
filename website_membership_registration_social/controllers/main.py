from odoo import _

from odoo.addons.website_membership_registration.controllers.main import (
    MembershipRegistrationController,
)


class MembershipRegistrationControllerSocial(MembershipRegistrationController):
    def _validate_membership_telegram(self, telegram):
        error_message, telegram_valid = "", True
        if telegram:
            telegram_valid = telegram and all(
                c.isalnum() or c in ["_", "@"] for c in telegram
            )
            if not telegram_valid:
                error_message = _("Telegram Username is invalid.")
        return telegram, telegram_valid, error_message

    def _get_error_message_list(self, validation_data, error_data):
        error_list = super(
            MembershipRegistrationControllerSocial, self
        )._get_error_message_list(validation_data, error_data)
        if not validation_data["member_telegram"]:
            error_list.append(error_data["member_telegram"])
        return error_list

    def _get_partner_and_validation_data(self, post):
        partner_data, validation_data, error_data = super(
            MembershipRegistrationControllerSocial, self
        )._get_partner_and_validation_data(post)
        (
            partner_data["member_telegram"],
            validation_data["member_telegram"],
            error_data["member_telegram"],
        ) = self._validate_membership_telegram(post["member_telegram"])
        return partner_data, validation_data, error_data

    def _get_new_member_vals_dict(self, partner_data):
        vals = super(
            MembershipRegistrationControllerSocial, self
        )._get_new_member_vals_dict(partner_data)
        if partner_data.get("member_telegram"):
            vals["telegram"] = partner_data["member_telegram"]
        return vals
