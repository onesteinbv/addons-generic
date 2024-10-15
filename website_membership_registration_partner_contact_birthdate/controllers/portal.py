from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalMembership(CustomerPortal):
    CustomerPortal.OPTIONAL_BILLING_FIELDS += ["birthdate_date"]
