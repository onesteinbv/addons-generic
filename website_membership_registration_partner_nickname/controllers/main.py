from odoo import _

from odoo.addons.website_membership_registration.controllers.main import (
    MembershipRegistrationController,
)


class MembershipRegistrationControllerNickname(MembershipRegistrationController):
    def _validate_member_nickname(self, nickname):
        error_message, nickname_valid = "", True
        if nickname:
            nickname_valid = nickname and all(
                c.isalnum() or c.isspace() for c in nickname
            )
            if not nickname_valid:
                error_message = _("Nickname is invalid.")
        return nickname, nickname_valid, error_message

    def _get_error_message_list(self, validation_data, error_data):
        error_list = super()._get_error_message_list(validation_data, error_data)
        if not validation_data["member_nickname"]:
            error_list.append(error_data["member_nickname"])
        return error_list

    def _get_partner_and_validation_data(self, post):
        partner_data, validation_data, error_data = (
            super()._get_partner_and_validation_data(post)
        )
        (
            partner_data["member_nickname"],
            validation_data["member_nickname"],
            error_data["member_nickname"],
        ) = self._validate_member_nickname(post.get("member_nickname", ""))
        return partner_data, validation_data, error_data

    def _get_new_member_vals_dict(self, partner_data):
        vals = super()._get_new_member_vals_dict(partner_data)
        if partner_data.get("member_nickname"):
            vals["nickname"] = partner_data["member_nickname"]
        return vals
