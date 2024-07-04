import logging

from odoo import Command, _, fields, http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)

try:
    from dns.exception import DNSException
except ImportError as err:
    _logger.debug(err)


class PortalController(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "app_count" in counters:
            app_count = request.env["argocd.application"].search_count([])
            values["app_count"] = app_count
        return values

    @http.route(
        ["/my/applications", "/my/applications/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_applications(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            "name": {"label": _("Name"), "order": "name desc"},
            "creation": {"label": _("Creation"), "order": "create_date desc"},
        }
        if not sortby:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]
        app_count = request.env["argocd.application"].search_count([])
        # pager
        pager = portal_pager(
            url="/my/applications",
            url_args={
                "sortby": sortby,
            },
            total=app_count,
            page=page,
            step=self._items_per_page,
        )
        apps = request.env["argocd.application"].search(
            [], order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        products = request.env["product.product"].search(
            [("application_template_id", "!=", False), ("sale_ok", "=", True)]
        )
        values.update(
            {
                "apps": apps.sudo(),  # We don't have access to the invoice lines without this
                "page_name": "Applications",
                "pager": pager,
                "default_url": "/my/applications",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "products": products.sudo(),
            }
        )
        return request.render("argocd_website.portal_my_applications", values)

    @http.route(
        ["/my/applications/<int:app_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_application_detail(self, app_id, **kw):
        try:
            app_sudo = self._document_check_access("argocd.application", app_id)
        except (AccessError, MissingError):
            return request.redirect("/my/applications")
        values = {
            "page_name": "Applications",
            "app": app_sudo,
            "message": kw.get("message"),
        }
        return request.render("argocd_website.portal_application_page", values)

    @http.route(
        ["/my/applications/<int:app_id>/request-delete"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_application_request_delete(self, app_id, **kw):
        try:
            app_sudo = self._document_check_access("argocd.application", app_id)
        except (AccessError, MissingError):
            return request.redirect("/my")
        app_sudo.request_destroy()
        return request.redirect("/my/applications/%s?message=request_deletion" % app_id)

    @http.route(
        ["/my/applications/<int:app_id>/confirm-delete"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_application_confirm_delete(self, app_id, **kw):
        try:
            app_sudo = self._document_check_access("argocd.application", app_id)
        except (AccessError, MissingError):
            return request.redirect("/my/applications")
        if not app_sudo.deletion_token:
            return request.redirect("/my/applications")
        if app_sudo.deletion_token != kw.get("token"):
            return request.render(
                "argocd_website.error_page", {"message": _("Invalid token")}
            )
        if fields.Datetime.now() > app_sudo.deletion_token_expiration:
            return request.render(
                "argocd_website.error_page", {"message": _("Token expired")}
            )

        if request.httprequest.method == "POST":
            try:
                app_sudo.confirm_destroy(kw.get("token"))
            except ValidationError as e:
                return request.render("argocd_website.error_page", {"message": str(e)})
            return request.redirect(
                "/my/applications/%s?message=pending_deletion" % app_id
            )

        values = {
            "page_name": "Applications",
            "app": app_sudo,
            "message": kw.get("message"),
        }

        return request.render(
            "argocd_website.portal_application_confirm_deletion_page", values
        )

    @http.route(
        ["/my/applications/<int:app_id>/domain-names"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_application_domain_names(self, app_id, **kw):
        return request.redirect("/my/applications")  # Temporary disable
        # pylint: disable=unreachable
        try:
            app_sudo = self._document_check_access("argocd.application", app_id)
        except (AccessError, MissingError):
            return request.redirect("/my/applications")
        current = app_sudo.value_ids.filtered(lambda kp: kp.key.startswith("domain"))
        values = {
            "page_name": "Applications",
            "app": app_sudo,
            "defaults": {kp.key: kp.value for kp in current},
        }

        if request.httprequest.method == "POST":
            message = "success"
            domain = kw.get("domain")

            # Process form and set new defaults
            custom_domains = {}
            if domain:
                custom_domains["domain"] = {"value": domain}
            values["defaults"]["domain"] = domain or ""
            for tag in app_sudo.tag_ids:
                domain = kw.get("domain_%s" % tag.id, "")
                values["defaults"]["domain_%s" % tag.key] = domain
                if not domain:
                    continue
                custom_domains["domain_%s" % tag.key] = {
                    "value": domain,
                    "tag_id": tag.id,
                }

            # Check DNS
            for key in custom_domains:
                try:
                    if not app_sudo.dns_cname_check(
                        custom_domains[key]["value"], custom_domains[key].get("tag_id")
                    ):  # Can still return False if inherited
                        message = "error"
                except (DNSException, ValidationError):
                    message = "error"
            values["message"] = message

            if message == "error":
                return request.render(
                    "argocd_website.portal_application_domain_names_page", values
                )

            # Unlink unset values
            unset_values = app_sudo.value_ids.filtered(
                lambda kp: kp.key not in custom_domains.keys()
            )
            unset_values.unlink()

            # Update and create new values
            new_values = []
            for key in custom_domains:
                existing_value = app_sudo.value_ids.filtered(lambda kp: kp.key == key)
                value = custom_domains[key]["value"]
                if existing_value:
                    existing_value.value = value
                else:
                    new_values.append({"key": key, "value": value})
            app_sudo.value_ids = [Command.create(val) for val in new_values]
            return request.redirect("/my/applications")
        return request.render(
            "argocd_website.portal_application_domain_names_page", values
        )
