import base64
import re

from werkzeug.exceptions import NotFound

from odoo import _, fields, http
from odoo.exceptions import ValidationError
from odoo.http import request


class MembershipRegistrationController(http.Controller):
    def _validate_membership_email(self, email):
        email_valid = True if re.match(r"[^@]+@[^@]+\.[^@]+", email) else False
        error_message = ""
        if not email_valid:
            error_message = _("A valid email address is required.")
        else:
            exists = (
                request.env["res.partner"]
                .sudo()
                .search(
                    [("email", "=ilike", email), ("membership_state", "!=", "none")],
                    limit=1,
                )
            )
            email_valid = True if not exists else False
            if not email_valid:
                error_message = _("Your email is already in our system.")
            else:
                exists = (
                    request.env["res.users"]
                    .sudo()
                    .search([("login", "=ilike", email)], limit=1)
                )
                email_valid = True if not exists else False
                if not email_valid:
                    error_message = _("Your email is already in our system.")

        return email, email_valid, error_message

    def _validate_membership_cv(self, cv):
        cv_valid = True
        error_message = ""
        cv_file = cv
        if cv:
            if (
                not request.website.membership_registration_cv_file_formats_supported
                == "*"
            ):
                for (
                    file_format
                ) in request.website.membership_registration_cv_file_formats_supported.split(
                    ","
                ):
                    if not cv.filename.endswith(file_format):
                        cv_valid = cv_file = False
                        error_message = _(
                            "Only %s files are accepted.",
                            request.website.membership_registration_cv_file_formats_supported,
                        )
                        break
            if cv_valid:
                cv_file = cv.stream.read()
                size = cv.stream.tell()
                if size > (
                    request.website.membership_registration_max_cv_file_size * 1048576
                ):
                    cv_valid = cv_file = False
                    error_message = _("File is too big.")
        return cv_file, cv_valid, error_message

    def _validate_membership_phone(self, phone):
        phone_valid = True if (not phone or re.match(r"^\+?[\d]+$", phone)) else False
        error_message = ""
        if not phone_valid:
            error_message = _(
                "Please, enter a valid phone number, or keep it blank if you wish."
            )
        return phone, phone_valid, error_message

    def _validate_membership_name(self, name):
        error_message = ""
        name_valid = name and all(c.isalnum() or c.isspace() for c in name)
        if not name_valid:
            error_message = _("Name is empty or invalid.")
        return name, name_valid, error_message

    def _validate_membership_product(self, product_id):
        product_valid = True
        error_message = ""
        if product_id:
            product = request.env["product.product"].sudo().browse(int(product_id))
            if not product.exists():
                error_message = _(
                    "The selected membership level is not a valid product"
                )
                product_valid = False
        else:
            error_message = _("Please, select a membership level.")
            product_valid = False
        return product_id, product_valid, error_message

    def _validate_membership_address(self, post):
        res = {
            "member_street": [post.get("member_street", ""), True, ""],
            "member_street2": [post.get("member_street2", ""), True, ""],
            "member_city": [post.get("member_city", ""), True, ""],
            "member_zip": [post.get("member_zip", ""), True, ""],
            "member_country_id": [post.get("member_country_id", ""), True, ""],
            "member_state_id": [post.get("member_state_id", ""), True, ""],
        }

        product = (
            post["membership_product_id"]
            and request.env["product.product"]
            .sudo()
            .browse(int(post["membership_product_id"]))
            or request.env["product.product"].sudo()
        )
        if product.exists() and product.list_price:
            if not post.get("member_street", False):
                res["member_street"][1] = False
                res["member_street"][2] = _("Street is missing")
            if not post.get("member_city", False):
                res["member_city"][1] = False
                res["member_city"][2] = _("City is missing")
            if not post.get("member_country_id", False):
                res["member_country_id"][1] = False
                res["member_country_id"][2] = _("Country is missing")
            else:
                country = request.env["res.country"].browse(
                    int(post["member_country_id"])
                )
                if country.state_required:
                    if not post.get("member_state_id", False):
                        res["member_state_id"][1] = False
                        res["member_state_id"][2] = _("State is missing")
                if country.zip_required:
                    if not post.get("member_zip", False):
                        res["member_zip"][1] = False
                        res["member_zip"][2] = _("ZIP Code is missing")

        return res

    def _validate_membership_groups(self, membership_group_list):
        return membership_group_list, True, ""

    def _get_errors_dict(self, validation_data):
        error_dict = {}
        if not validation_data["member_street"]:
            error_dict["member_street"] = "missing"
        if not validation_data["member_street2"]:
            error_dict["member_street2"] = "missing"
        if not validation_data["member_city"]:
            error_dict["member_city"] = "missing"
        if not validation_data["member_zip"]:
            error_dict["member_zip"] = "missing"
        if not validation_data["member_country_id"]:
            error_dict["member_country_id"] = "missing"
        if not validation_data["member_state_id"]:
            error_dict["member_state_id"] = "missing"
        return error_dict

    def _get_error_message_list(self, validation_data, error_data):
        error_list = []
        if not validation_data["member_email"]:
            error_list.append(error_data["member_email"])
        if not validation_data["member_name"]:
            error_list.append(error_data["member_name"])
        if not validation_data["member_phone"]:
            error_list.append(error_data["member_phone"])
        if not validation_data["membership_product_id"]:
            error_list.append(error_data["membership_product_id"])
        if not validation_data["member_street"]:
            error_list.append(error_data["member_street"])
        if not validation_data["member_street2"]:
            error_list.append(error_data["member_street2"])
        if not validation_data["member_city"]:
            error_list.append(error_data["member_city"])
        if not validation_data["member_zip"]:
            error_list.append(error_data["member_zip"])
        if not validation_data["member_country_id"]:
            error_list.append(error_data["member_country_id"])
        if not validation_data["member_state_id"]:
            error_list.append(error_data["member_state_id"])
        if not validation_data["member_cv"]:
            error_list.append(error_data["member_cv"])
        return error_list

    def _get_partner_and_validation_data(self, post):
        partner_data = {}
        validation_data = {}
        error_data = {}
        partner_data["website_description"] = post.get("website_description", "")
        (
            partner_data["member_email"],
            validation_data["member_email"],
            error_data["member_email"],
        ) = self._validate_membership_email(post["member_email"])
        (
            partner_data["member_name"],
            validation_data["member_name"],
            error_data["member_name"],
        ) = self._validate_membership_name(post["member_name"])
        (
            partner_data["member_phone"],
            validation_data["member_phone"],
            error_data["member_phone"],
        ) = self._validate_membership_phone(post["member_phone"])
        (
            partner_data["member_cv"],
            validation_data["member_cv"],
            error_data["member_cv"],
        ) = self._validate_membership_cv(post.get("member_cv", False))
        (
            partner_data["application_date"],
            validation_data["application_date"],
            error_data["application_date"],
        ) = (fields.Datetime.now(), True, "")
        (
            partner_data["membership_product_id"],
            validation_data["membership_product_id"],
            error_data["membership_product_id"],
        ) = self._validate_membership_product(post["membership_product_id"])

        address_data = self._validate_membership_address(post)

        (
            partner_data["member_street"],
            validation_data["member_street"],
            error_data["member_street"],
        ) = address_data["member_street"]
        (
            partner_data["member_street2"],
            validation_data["member_street2"],
            error_data["member_street2"],
        ) = address_data["member_street2"]
        (
            partner_data["member_city"],
            validation_data["member_city"],
            error_data["member_city"],
        ) = address_data["member_city"]
        (
            partner_data["member_zip"],
            validation_data["member_zip"],
            error_data["member_zip"],
        ) = address_data["member_zip"]
        (
            partner_data["member_country_id"],
            validation_data["member_country_id"],
            error_data["member_country_id"],
        ) = address_data["member_country_id"]
        (
            partner_data["member_state_id"],
            validation_data["member_state_id"],
            error_data["member_state_id"],
        ) = address_data["member_state_id"]

        membership_group_ids = request.env["membership.group"].search(
            [("is_published", "=", True)]
        )
        membership_group_list = {}
        for membership_group in membership_group_ids:
            if "membership_group_%s_follow" % membership_group.id in post:
                membership_group_list[
                    "membership_group_%s_follow" % membership_group.id
                ] = (
                    post["membership_group_%s_follow" % membership_group.id] == "on"
                    or False
                )
            if "membership_group_%s_collaborate" % membership_group.id in post:
                membership_group_list[
                    "membership_group_%s_collaborate" % membership_group.id
                ] = (
                    post["membership_group_%s_collaborate" % membership_group.id]
                    == "on"
                    or False
                )
        (
            partner_data["membership_group_data"],
            validation_data["membership_group_data"],
            error_data["membership_group_data"],
        ) = self._validate_membership_groups(membership_group_list)

        return partner_data, validation_data, error_data

    def _get_new_member_vals_dict(self, partner_data):
        vals = {
            "name": partner_data["member_name"],
            "street": partner_data["member_street"],
            "street2": partner_data["member_street2"],
            "city": partner_data["member_city"],
            "zip": partner_data["member_zip"],
            "country_id": partner_data["member_country_id"]
            and int(partner_data["member_country_id"])
            or None,
            "state_id": partner_data["member_state_id"]
            and int(partner_data["member_state_id"])
            or None,
            "email": partner_data["member_email"],
            "phone": partner_data["member_phone"],
            "website_id": request.website.id,
            "company_id": request.env.company.id,
            "website_description": partner_data["website_description"],
            "membership_application_date": fields.Date.today(),
        }
        partner_category = request.env.ref(
            "website_membership_registration.res_partner_category_website_form", False
        )
        if partner_category:
            vals["category_id"] = [(4, partner_category.id)]
        return vals

    def _set_partner_membership_group(self, partner, partner_data):
        membership_groups = request.env["membership.group"].search(
            [("is_published", "=", True)]
        )
        membership_group_data = self._get_membership_group_data(
            membership_groups, partner_data["membership_group_data"]
        )
        membership_group_member_data_list = self._get_membership_group_member_data_list(
            membership_group_data, partner_data
        )
        partner.write(
            {
                "membership_group_member_ids": [
                    (0, 0, membership_group_data)
                    for membership_group_data in membership_group_member_data_list
                ]
            }
        )

    def _get_order_vals(self, partner, product):
        return {
            "partner_id": partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_qty": 1,
                        "price_unit": 100.0,
                    },
                )
            ],
        }

    def _get_membership_group_data(self, membership_groups, data):
        follow_membership_groups = membership_groups.filtered(
            lambda c: "membership_group_%s_follow" % c.id in data
            and data["membership_group_%s_follow" % c.id]
        )
        contribute_membership_groups = membership_groups.filtered(
            lambda c: "membership_group_%s_collaborate" % c.id in data
            and data["membership_group_%s_collaborate" % c.id]
        )
        return {
            "follow": follow_membership_groups,
            "collaborate": contribute_membership_groups,
        }

    def _get_membership_group_member_data_list(
        self, membership_group_data, partner_data
    ):
        membership_groups = self._get_all_membership_groups(membership_group_data)
        res = []
        for membership_group in membership_groups:
            res.append(
                self._get_membership_group_member_data_dict(
                    membership_group, membership_group_data, partner_data
                )
            )
        return res

    def _get_all_membership_groups(self, membership_group_data):
        return membership_group_data["follow"] | membership_group_data["collaborate"]

    def _get_membership_group_member_data_dict(
        self, membership_group, membership_group_data, partner_data
    ):
        return {
            "group_id": membership_group.id,
            "on_mailing_list": membership_group in membership_group_data["follow"]
            and True
            or False,
            "wants_to_collaborate": membership_group
            in membership_group_data["collaborate"]
            and True
            or False,
        }

    def _get_membership_form_page_vals(
        self, is_logged, product, old_data=None, error_message="", errors=None
    ):
        membership_products = (
            request.env["product.product"]
            .sudo()
            .search(
                [
                    ("membership", "=", True),
                    ("type", "=", "service"),
                    ("visible_on_membership_registration_page", "=", True),
                ]
            )
        )

        membership_groups = request.env["membership.group"].search(
            [("is_published", "=", True)]
        )
        membership_groups_follow_checked = {}
        membership_groups_collaborate_checked = {}
        for c in membership_groups:
            membership_groups_follow_checked.update({c.id: False})
            membership_groups_collaborate_checked.update({c.id: False})
        if not old_data:
            old_data = {}
        if "membership_group_data" in old_data:
            for c in membership_groups:
                if (
                    "membership_group_%s_follow" % c.id
                    in old_data["membership_group_data"]
                ):
                    membership_groups_follow_checked.update({c.id: True})
                if (
                    "membership_group_%s_collaborate" % c.id
                    in old_data["membership_group_data"]
                ):
                    membership_groups_collaborate_checked.update({c.id: True})
            old_data.pop("membership_group_data")
        membership_group_style = (
            request.website.membership_registration_page_membership_group_style
        )
        if not errors:
            errors = {}
        res = {
            "is_logged": is_logged,
            "member_name": "",
            "member_email": "",
            "member_phone": "",
            "membership_group_style": membership_group_style,
            "member_street": "",
            "member_street2": "",
            "member_zip": "",
            "member_city": "",
            "member_country_id": "",
            "member_state_id": "",
            "website_description": "",
            "country_id": request.env["res.country"],
            "state_id": request.env["res.country.state"],
            "membership_products": membership_products,
            "membership_product_id": product.id if product else None,
            "show_address_div": (
                membership_products
                and membership_products[0].list_price
                and True
                or False
            )
            or False,
            "membership_groups": membership_groups,
            "countries": request.env["res.country"].sudo().search([]),
            "country_states": request.env["res.country.state"],
            "membership_groups_follow_checked": membership_groups_follow_checked,
            "membership_groups_collaborate_checked": membership_groups_collaborate_checked,
            "error_message": error_message,
            "error": errors,
        }
        res.update(old_data)
        if res.get("member_country_id", False):
            res["member_country_id"] = request.env["res.country"].browse(
                int(res["member_country_id"])
            )
        else:
            if request.website.company_id.country_id:
                res["member_country_id"] = request.website.company_id.country_id.id
        if res.get("member_state_id", False):
            res["member_state_id"] = request.env["res.country.state"].browse(
                int(res["member_state_id"])
            )
        else:
            if res["member_country_id"] == request.env.ref("base.nl").id:
                res["member_state_id"] = request.env.ref("base.state_nl_nb").id
        return res

    @http.route(
        ["/membership-registration", "/membership-registration/<int:product_id>"],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
    )
    def membership_registration_form(self, product_id=None):
        if not request.website.allow_membership_registration:
            return http.request.not_found()

        is_logged = not request.env.user._is_public()
        is_member = is_logged and request.env.user.membership_state != "none"

        if is_member:
            return request.render(
                "website_membership_registration.membership_already_exists_page"
            )
        product = (
            request.env["product.product"].sudo().browse(product_id)
            if product_id
            else None
        )
        vals = self._get_membership_form_page_vals(
            is_logged,
            product,
            request.session.get("old_registration_data", {}),
            request.session.get("error_message", ""),
            request.session.get("error", {}),
        )
        if request.session.get("old_registration_data", {}):
            request.session.pop("old_registration_data")
        if request.session.get("error_message", ""):
            request.session.pop("error_message")
        if request.session.get("error", ""):
            request.session.pop("error", "")
        return request.render(
            "website_membership_registration.membership_registration_page", vals
        )

    @http.route(
        ["/apply-for-membership"],
        type="http",
        methods=["POST"],
        auth="public",
        csrf=False,
        website=True,
    )
    def post_membership_registration_form(self, **post):
        if not request.website.allow_membership_registration:
            return http.request.not_found()

        (
            partner_data,
            validation_data,
            error_data,
        ) = self._get_partner_and_validation_data(post)
        error_message = "\r".join(
            self._get_error_message_list(validation_data, error_data)
        )
        errors = self._get_errors_dict(validation_data)
        if not error_message:
            product = (
                request.env["product.product"]
                .sudo()
                .browse(int(post["membership_product_id"]))
            )
            partner_vals = self._get_new_member_vals_dict(partner_data)
            partner = (
                request.env["res.partner"]
                .sudo()
                .search([("email", "=ilike", partner_vals["email"])], limit=1)
            )
            sale_order = request.env["sale.order"]
            try:
                if not partner:
                    partner = request.env["res.partner"].sudo().create(partner_vals)
                else:
                    partner.write(partner_vals)
                self._set_partner_membership_group(partner, partner_data)
                if partner_data.get("member_cv"):
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": post["member_cv"].filename,
                            "res_model": "res.partner",
                            "res_id": partner.id,
                            "datas": base64.b64encode(partner_data.get("member_cv")),
                        }
                    )
                sale_order = partner.create_membership_sale_order(
                    product, product.list_price
                )
            except Exception as e:
                error_message = str(e)
                self._handle_errors(partner_data, error_message, errors)
            if request.session.get("old_registration_data", {}):
                request.session.pop("old_registration_data")
            if request.session.get("error_message", ""):
                request.session.pop("error_message")
            if request.session.get("error", ""):
                request.session.pop("error", "")
            if sale_order.amount_total:
                # Generate payment link
                ctx = request.env.context.copy()
                ctx.update(
                    {
                        "active_id": sale_order.id,
                        "active_model": "sale.order",
                    }
                )
                link_wizard = (
                    request.env["payment.link.wizard"]
                    .sudo()
                    .with_context(ctx)
                    .create({})
                )
                link_wizard._compute_link()
                return request.redirect(link_wizard.link)
            else:
                sale_order.action_confirm()
                sale_order.with_context(
                    raise_if_nothing_to_invoice=False
                )._create_invoices()
                partner.send_membership_verification_email()
            return request.redirect("/apply-for-membership-success")
        self._handle_errors(partner_data, error_message, errors)

    def _handle_errors(self, partner_data, error_message, errors):
        partner_data.pop("application_date", None)
        request.session.update(
            {
                "old_registration_data": partner_data,
                "error_message": error_message,
                "error": errors,
            }
        )
        return request.redirect("/membership-registration")

    @http.route(
        ["/apply-for-membership-success"],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def apply_for_membership_success(self):
        if not request.website.allow_membership_registration:
            return http.request.not_found()
        return request.render(
            "website_membership_registration.membership_registration_success_page"
        )

    @http.route(
        ["/apply-for-membership-verify"],
        type="http",
        methods=["GET"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def apply_for_membership_verify(self, partner_id, token, email):
        if not request.website.allow_membership_registration:
            return http.request.not_found()
        partner = request.env["res.partner"].sudo().browse(int(partner_id))
        if not partner.exists():
            return request.render(
                "website_membership_registration.membership_registration_verify_error_page",
                {"error": _("Email address verification failed.")},
            )
        try:
            partner.verify_email(email, token)
        except ValidationError as error:
            return request.render(
                "website_membership_registration.membership_registration_verify_error_page",
                {"error": error.name},
            )

        invoices = partner.member_lines.mapped("account_invoice_line").mapped("move_id")
        for invoice in invoices:
            if invoice.state == "draft":
                invoice.action_post()
        if not partner.user_ids or (
            not any(user.has_group("base.group_user") for user in partner.user_ids)
            and not any(
                user.has_group("base.group_portal") for user in partner.user_ids
            )
        ):
            wizard = (
                request.env["portal.wizard"]
                .with_user(request.env.ref("base.user_admin").id)
                .create(
                    {
                        "partner_ids": [(6, 0, partner.ids)],
                    }
                )
            )
            wizard.user_ids.action_grant_access()
            partner.create_member_applicant()
        return request.render(
            "website_membership_registration.membership_registration_verify_success_page"
        )

    @http.route(["/membership-registration/config/website"], type="json", auth="user")
    def _change_membership_registration_website_config(self, **options):
        if not request.env.user.has_group("website.group_website_restricted_editor"):
            raise NotFound()

        current_website = request.env["website"].get_current_website()
        # Restrict options we can write to.
        writable_fields = {
            "membership_registration_page_membership_group_style",
            "membership_registration_max_cv_file_size",
            "membership_registration_cv_file_formats_supported",
        }
        # Default membership_group layout to list.
        if (
            "membership_registration_page_membership_group_style" in options
            and not options["membership_registration_page_membership_group_style"]
        ):
            options["membership_registration_page_membership_group_style"] = "list"
        # Default max cv file size to 3.
        if (
            "membership_registration_max_cv_file_size" in options
            and not options["membership_registration_max_cv_file_size"]
        ):
            options["membership_registration_max_cv_file_size"] = 3
        # Default file format supported to '.pdf'.
        if (
            "membership_registration_cv_file_formats_supported" in options
            and not options["membership_registration_cv_file_formats_supported"]
        ):
            options["membership_registration_cv_file_formats_supported"] = ".pdf"

        write_vals = {k: v for k, v in options.items() if k in writable_fields}
        if write_vals:
            current_website.write(write_vals)
