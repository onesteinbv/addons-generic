from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalMembership(CustomerPortal):
    CustomerPortal.OPTIONAL_BILLING_FIELDS += [
        "github_login",
        "gitlab_username",
        "gitlab_email",
    ]
