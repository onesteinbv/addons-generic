from odoo import _
from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalMembership(CustomerPortal):
    CustomerPortal.OPTIONAL_BILLING_FIELDS += ["nickname", "website_published"]

    @route()
    def account(self, redirect=None, **post):
        if (
            request.httprequest.path == "/my/account"
            and post
            and request.httprequest.method == "POST"
        ):
            if not post.get("website_published"):
                post["website_published"] = False
            else:
                post["website_published"] = True
        return super().account(redirect=redirect, **post)

    def details_form_validate(self, data, partner_creation=False):
        error, error_message = super(
            CustomerPortalMembership, self
        ).details_form_validate(data, partner_creation=partner_creation)
        if data.get("nickname") and not (
            all(c.isalnum() or c.isspace() for c in data.get("nickname"))
        ):
            error["nickname"] = "error"
            error_message.append(_("Nickname is invalid."))
        return error, error_message
