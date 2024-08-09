from odoo import _, fields, http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PortalSubscription(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "subscription_count" in counters:
            subscription_model = request.env["sale.subscription"]
            subscription_count = (
                subscription_model.search_count(self._get_filter_domain({}))
                if subscription_model.check_access_rights("read", raise_exception=False)
                else 0
            )
            values["subscription_count"] = subscription_count
        return values

    def _subscription_get_page_view_values(self, subscription, access_token, **kwargs):
        values = {
            "page_name": "Subscriptions",
            "subscription": subscription,
        }
        return self._get_page_view_values(
            subscription,
            access_token,
            values,
            "my_subscriptions_history",
            False,
            **kwargs
        )

    def _get_filter_domain(self, kw):
        return []

    @http.route(
        ["/my/subscriptions", "/my/subscriptions/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_subscriptions(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        subscription_obj = request.env["sale.subscription"]
        # Avoid error if the user does not have access.
        if not subscription_obj.check_access_rights("read", raise_exception=False):
            return request.redirect("/my")
        domain = self._get_filter_domain(kw)
        searchbar_sortings = {
            "date": {"label": _("Date"), "order": "recurring_next_date desc"},
            "name": {"label": _("Name"), "order": "name desc"},
            "code": {"label": _("Reference"), "order": "code desc"},
        }
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]
        # count for pager
        subscription_count = subscription_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/subscriptions",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
            },
            total=subscription_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager and archive selected
        subscriptions = subscription_obj.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_subscriptions_history"] = subscriptions.ids[:100]
        values.update(
            {
                "date": date_begin,
                "subscriptions": subscriptions,
                "page_name": "Subscriptions",
                "pager": pager,
                "default_url": "/my/subscriptions",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("subscription_portal.portal_my_subscriptions", values)

    @http.route(
        ["/my/subscriptions/<int:sale_subscription_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_subscription_detail(
        self, sale_subscription_id, access_token=None, **kw
    ):
        try:
            subscription_sudo = self._document_check_access(
                "sale.subscription", sale_subscription_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._subscription_get_page_view_values(
            subscription_sudo, access_token, **kw
        )
        return request.render("subscription_portal.portal_subscription_page", values)

    @http.route(
        ["/my/subscriptions/<int:sub_id>/start-cancellation"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_subscription_start_cancellation(self, sub_id, **kw):
        try:
            sub_sudo = self._document_check_access("sale.subscription", sub_id)
        except (AccessError, MissingError):
            return request.redirect("/my")
        sub_sudo.start_cancellation()
        return request.redirect(
            "/my/subscriptions/%s?success=start_cancellation" % sub_id
        )

    @http.route(
        ["/my/subscriptions/<int:sub_id>/confirm-cancellation"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_subscription_confirm_cancellation(self, sub_id, **kw):
        try:
            sub_sudo = self._document_check_access("sale.subscription", sub_id)
        except (AccessError, MissingError):
            return request.redirect("/my/applications")
        if not sub_sudo.cancellation_token:
            return request.redirect("/my/applications")
        if sub_sudo.cancellation_token != kw.get("token"):
            return request.render(
                "subscription_portal.error_page", {"message": _("Invalid token")}
            )
        if fields.Datetime.now() > sub_sudo.cancellation_token_expiration:
            return request.render(
                "subscription_portal.error_page", {"message": _("Token expired")}
            )

        if request.httprequest.method == "POST":
            try:
                sub_sudo.confirm_cancellation(kw.get("token"))
            except ValidationError as e:
                return request.render(
                    "subscription_portal.error_page", {"message": str(e)}
                )
            return request.redirect("/my/subscriptions/%s" % sub_id)

        values = {"page_name": "Subscriptions", "subscription": sub_sudo}

        return request.render(
            "subscription_portal.portal_subscription_confirm_cancellation_page", values
        )
