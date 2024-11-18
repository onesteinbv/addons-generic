import datetime

from odoo import _

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalMembership(CustomerPortal):
    CustomerPortal.OPTIONAL_BILLING_FIELDS += ["birthdate_date"]

    def details_form_validate(self, data, partner_creation=False):
        error, error_message = super(
            CustomerPortalMembership, self
        ).details_form_validate(data, partner_creation=partner_creation)
        if data.get("birthdate_date"):
            try:
                datetime.datetime.strptime(data.get("birthdate_date"), "%Y-%m-%d")
            except ValueError:
                error["birthdate_date"] = "error"
                error_message.append(_("Birth Date is invalid."))
        return error, error_message
