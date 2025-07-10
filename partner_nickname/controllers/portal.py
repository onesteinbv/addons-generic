from odoo import _

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalNickname(CustomerPortal):
    def _get_optional_fields(self):
        # EXTEND 'portal'
        optional_fields = super()._get_optional_fields()
        optional_fields += ["nickname"]
        return optional_fields

    def details_form_validate(self, data, partner_creation=False):
        error, error_message = super(
            CustomerPortalNickname, self
        ).details_form_validate(data, partner_creation=partner_creation)
        if data.get("nickname") and not (
            all(c.isalnum() or c.isspace() for c in data.get("nickname"))
        ):
            error["nickname"] = "error"
            error_message.append(_("Nickname is invalid."))
        return error, error_message
