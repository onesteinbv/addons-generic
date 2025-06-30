from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalWebsitePrivacy(CustomerPortal):
    CustomerPortal.MANDATORY_BILLING_FIELDS += ["website_privacy"]
    CustomerPortal.OPTIONAL_BILLING_FIELDS += [
        "show_email",
        "show_address",
        "show_phone",
        "show_website",
        "is_published",
    ]

    @route()
    def account(self, redirect=None, **post):
        if (
            request.httprequest.path == "/my/account"
            and post
            and request.httprequest.method == "POST"
        ):
            if not post.get("is_published"):
                post["is_published"] = False
            else:
                post["is_published"] = True
            if not post.get("show_email"):
                post["show_email"] = False
            else:
                post["show_email"] = True
            if not post.get("show_address"):
                post["show_address"] = False
            else:
                post["show_address"] = True
            if not post.get("show_phone"):
                post["show_phone"] = False
            else:
                post["show_phone"] = True
            if not post.get("show_website"):
                post["show_website"] = False
            else:
                post["show_website"] = True
        return super().account(redirect=redirect, **post)
