from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalWebsiteDescription(CustomerPortal):
    def _get_optional_fields(self):
        # EXTEND 'portal'
        optional_fields = super()._get_optional_fields()
        optional_fields += ["website_description"]
        return optional_fields
