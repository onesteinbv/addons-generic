import logging

from odoo import _, http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager

_logger = logging.getLogger(__name__)


class CustomerPortalController(CustomerPortal):
    def _get_reseller_partner(self):
        """Get the reseller partner (company) for the current user.
        Returns the parent partner if it's a reseller, otherwise the user's partner if it's a reseller.
        """
        user = request.env.user
        if user.partner_id.parent_id and user.partner_id.parent_id.is_reseller:
            return user.partner_id.parent_id
        elif user.partner_id.is_reseller:
            return user.partner_id
        return None

    def _check_reseller_customer_access(self, customer_id):
        """Check if the current user has access to the specified customer.
        Returns the customer record if access is granted, raises AccessError otherwise.
        """
        # Check record rules to ensure the user has access to the customer
        try:
            self._document_check_access("res.partner", customer_id)
        except (AccessError, MissingError) as err:
            raise AccessError(
                _("You don't have permission to access this partner.")
            ) from err

        # Additionally, we check if the user is associated with a reseller or is a reseller themselves
        reseller_partner = self._get_reseller_partner()
        if not reseller_partner:
            raise AccessError(_("You don't have permission to access this page."))

        # We can assume the partner exists at this point, since _document_check_access would have raised a MissingError otherwise
        customer = request.env["res.partner"].browse(customer_id)

        # Not strictly necessary as the record rules should already prevent this
        if customer.reseller_id != reseller_partner:
            raise AccessError(_("You don't have permission to access this customer."))

        return customer.sudo()  # We return sudoed record to bypass access rights in the templates, since we have already checked access

    def _validate_form_data(self, data):
        errors = {}
        required_fields = {
            "name": _("Company Name"),
            "email": _("Email"),
            "street": _("Street"),
            "city": _("City"),
            "zip": _("ZIP"),
            "company_registry": _("Chamber of Commerce number"),
        }
        for field, label in required_fields.items():
            if not data.get(field):
                errors[field] = _("%s is required.") % label
        return errors

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        reseller_partner = self._get_reseller_partner()
        if reseller_partner and "customer_count" in counters:
            customer_count = request.env["res.partner"].search_count(
                [("reseller_id", "=", reseller_partner.id)]
            )
            values["customer_count"] = customer_count
        return values

    @http.route(
        ["/my/customers", "/my/customers/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_customers(self, page=1, sortby=None, **kw):
        reseller_partner = self._get_reseller_partner()
        if not reseller_partner:
            return request.not_found()

        values = self._prepare_portal_layout_values()
        searchbar_sortings = {
            "name": {"label": _("Name"), "order": "name asc"},
            "creation": {"label": _("Creation Date"), "order": "create_date desc"},
            "city": {"label": _("City"), "order": "city asc"},
        }
        if not sortby:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]

        # We apply the reseller filter here which is not necessary for access control (as it is already enforced by the record rules), it's just an UX improvement
        domain = [("reseller_id", "=", reseller_partner.id)]
        customer_count = request.env["res.partner"].search_count(domain)

        # pager
        pager = portal_pager(
            url="/my/customers",
            url_args={
                "sortby": sortby,
            },
            total=customer_count,
            page=page,
            step=self._items_per_page,
        )

        customers = request.env["res.partner"].search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )

        values.update(
            {
                "customers": customers,
                "page_name": "Customers",
                "pager": pager,
                "default_url": "/my/customers",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("argocd_website.portal_my_customers", values)

    @http.route(
        ["/my/customers/<int:customer_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_customer_detail(self, customer_id, **kw):
        try:
            customer = self._check_reseller_customer_access(customer_id)
        except (AccessError, MissingError):
            return request.redirect("/my/customers")

        # Get subscriptions for this customer
        subscriptions = request.env["sale.subscription"].search(
            [
                ("end_partner_id", "=", customer_id),
                ("stage_id.type", "!=", "draft"),
                ("stage_id", "!=", False),
            ]
        )

        # Get applications for this customer
        applications = request.env["argocd.application"].search(
            [("partner_id", "=", customer_id)]
        )

        values = {
            "page_name": "Customers",
            "customer": customer,
            "subscriptions": subscriptions,
            "applications": applications,
            "message": kw.get("message"),
        }
        return request.render("argocd_website.portal_customer_detail", values)

    @http.route(
        ["/my/customers/create"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_customer_create(self, **post):
        reseller_partner = self._get_reseller_partner()
        if not reseller_partner:
            return request.not_found()

        # Handle return parameter
        return_param = request.params.get("return")

        values = {
            "page_name": "Customers",
            "countries": request.env["res.country"].search([]),
            "mode": "create",
            "form_data": post or {},
            "errors": {},
        }
        errors = values["errors"]

        if request.httprequest.method == "POST":
            # Validate required fields
            errors.update(self._validate_form_data(post))
            if errors:
                return request.render("argocd_website.portal_customer_form", values)

            try:
                # Create the customer
                customer_vals = {
                    "name": post.get("name"),
                    "email": post.get("email"),
                    "phone": post.get("phone"),
                    "street": post.get("street"),
                    "city": post.get("city"),
                    "zip": post.get("zip"),
                    "company_registry": post.get("company_registry"),
                    "reseller_id": reseller_partner.id,
                    "company_type": "company",
                    "lang": request.env.user.lang,  # FIXME: We assume the customer has the same language as the user (which is not always the case)
                }

                if post.get("country_id"):
                    customer_vals["country_id"] = int(post.get("country_id"))

                customer = request.env["res.partner"].sudo().create(customer_vals)

                # Handle return parameter if provided
                if return_param == "signup":
                    return request.redirect(
                        f"/application/signup?customer_id={customer.id}"
                    )

                return request.redirect(f"/my/customers/{customer.id}?message=created")
            except (ValidationError, UserError) as e:
                values.update({"errors": {"general": str(e)}, "form_data": post})
                return request.render("argocd_website.portal_customer_form", values)
        return request.render("argocd_website.portal_customer_form", values)

    @http.route(
        ["/my/customers/<int:customer_id>/edit"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_my_customer_edit(self, customer_id, **post):
        try:
            customer = self._check_reseller_customer_access(customer_id)
        except (AccessError, MissingError):
            return request.redirect("/my/customers")

        values = {
            "page_name": "Customers",
            "customer": customer,
            "countries": request.env["res.country"].search([]),
            "mode": "edit",
            "errors": {},
            "form_data": post or {},
        }

        if request.httprequest.method == "POST":
            errors = values["errors"]

            # Validate required fields
            errors.update(self._validate_form_data(post))

            if errors:
                return request.render("argocd_website.portal_customer_form", values)

            try:
                # Update the customer
                update_vals = {
                    "name": post.get("name"),
                    "email": post.get("email"),
                    "phone": post.get("phone"),
                    "street": post.get("street"),
                    "city": post.get("city"),
                    "zip": post.get("zip"),
                    "company_registry": post.get("company_registry"),
                }

                if post.get("country_id"):
                    update_vals["country_id"] = int(post.get("country_id"))

                customer.write(update_vals)

                return request.redirect(f"/my/customers/{customer.id}?message=updated")
            except (ValidationError, UserError) as e:
                errors["general"] = str(e)
                return request.render("argocd_website.portal_customer_form", values)

        # Pre-fill form with customer data
        values["form_data"] = {
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "street": customer.street,
            "city": customer.city,
            "zip": customer.zip,
            "country_id": customer.country_id.id if customer.country_id else False,
            "company_registry": customer.company_registry,
        }

        return request.render("argocd_website.portal_customer_form", values)

    @http.route(
        ["/my/customers/<int:customer_id>/archive"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_my_customer_archive(self, customer_id, **post):
        try:
            customer = self._check_reseller_customer_access(customer_id)
        except (AccessError, MissingError):
            return request.redirect("/my/customers")

        # Check if customer has active subscriptions
        active_subscriptions = request.env["sale.subscription"].search_count(
            [
                ("end_partner_id", "=", customer_id),
                ("stage_id.type", "=", "in_progress"),
            ]
        )

        if active_subscriptions > 0:
            return request.redirect(
                f"/my/customers/{customer_id}?message=has_active_subscriptions"
            )

        try:
            customer.active = False
            return request.redirect("/my/customers?message=archived")
        except (ValidationError, UserError) as e:
            _logger.exception("Error archiving customer %s: %s", customer_id, str(e))
            return request.redirect(
                f"/my/customers/{customer_id}?message=archive_error"
            )
