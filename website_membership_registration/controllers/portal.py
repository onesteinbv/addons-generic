from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
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
