from odoo import _

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalWebsitePrivacyNickname(CustomerPortal):
    def details_form_validate(self, data, partner_creation=False):
        error, error_message = super(
            CustomerPortalWebsitePrivacyNickname, self
        ).details_form_validate(data, partner_creation=partner_creation)
        if (
            data.get("website_privacy")
            and data["website_privacy"] == "nickname"
            and not data.get("nickname")
        ):
            error["nickname"] = "error"
            error_message.append(
                _(
                    "Nickname should be specified if Website Privacy is set to Use Nickname"
                )
            )
        return error, error_message
