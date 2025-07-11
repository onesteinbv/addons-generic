from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalWebsitePrivacy(CustomerPortal):
    def _get_optional_fields(self):
        # EXTEND 'portal'
        optional_fields = super()._get_optional_fields()
        optional_fields.extend(
            [
                "show_email",
                "show_address",
                "show_phone",
                "show_website",
                "is_published",
                "website_privacy",
            ]
        )
        return optional_fields

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
