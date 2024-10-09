from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalWebsiteDescription(CustomerPortal):
    CustomerPortal.OPTIONAL_BILLING_FIELDS += ["website_description"]
