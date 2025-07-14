from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalMembership(CustomerPortal):
    def _get_optional_fields(self):
        # EXTEND 'portal'
        optional_fields = super()._get_optional_fields()
        optional_fields.extend(
            [
                "github_login",
                "gitlab_username",
                "gitlab_email",
            ]
        )
        return optional_fields
