from odoo import _

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalMembership(CustomerPortal):
    def _get_optional_fields(self):
        # EXTEND 'portal'
        optional_fields = super()._get_optional_fields()
        optional_fields += ["telegram"]
        return optional_fields

    def details_form_validate(self, data, partner_creation=False):
        error, error_message = super(
            CustomerPortalMembership, self
        ).details_form_validate(data, partner_creation=partner_creation)
        if data.get("telegram") and not (
            all(c.isalnum() or c in ["_", "@"] for c in data["telegram"])
        ):
            error["telegram"] = "error"
            error_message.append(_("Telegram username is invalid."))
        return error, error_message
