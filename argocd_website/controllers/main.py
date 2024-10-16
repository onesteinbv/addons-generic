import re

from odoo import _, api, fields
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route


class MainController(Controller):
    def _validate(self, post, captcha_enabled, is_public, is_reseller):
        if captcha_enabled:
            try:
                request.env["librecaptcha"].answer(
                    post["captcha_id"], post["captcha_answer"], raise_exception=True
                )
            except ValidationError as e:
                return {"subject": "captcha", "message": str(e)}

        if is_public or is_reseller:
            if not post["email"]:
                return {"subject": "email", "message": _("Email Address is required.")}
            if not post["name"]:
                return {"subject": "name", "message": _("Company Name is required.")}
            if not post["street_name"]:
                return {"subject": "street_name", "message": _("Street is required.")}
            if not post["street_number"]:
                return {
                    "subject": "street_number",
                    "message": _("Street Number is required."),
                }
            if not post["zip"]:
                return {"subject": "zip", "message": _("Zip is required.")}
            if not post["city"]:
                return {"subject": "city", "message": _("City is required.")}
            if not post["company_registry"]:
                return {
                    "subject": "company_registry",
                    "message": _("CoC number is required."),
                }
            if not re.match(
                "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",
                post["email"],
            ):
                return {"subject": "email", "message": _("Invalid email address.")}

        if "terms_of_use" not in post:
            return {
                "subject": "terms_of_use",
                "message": _("Please accept the terms of use."),
            }

        if is_public:
            existing_users = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", post["email"])], count=True)
            )
            if existing_users:
                return {
                    "subject": "email",
                    "message": _("Email address already in use."),
                }
        return False

    @route(
        "/application/update_subscription_product",
        type="json",
        auth="public",
        website=True,
    )
    def update_subscription_product(self, product_template_id, combination):
        website = request.website.sudo()
        website.update_subscription_product(product_template_id, combination)

    @route(
        "/application/remove_subscription_product",
        type="json",
        auth="public",
        website=True,
    )
    def remove_subscription_product(self, product_template_id):
        website = request.website.sudo()
        website.remove_subscription_product(product_template_id)

    @route(
        "/application/get_subscription_details",
        type="json",
        auth="public",
        website=True,
    )
    def get_subscription_details(self):
        website = request.website.sudo()
        sub = website.ensure_subscription()
        currency = sub.currency_id
        return {
            "currency_id": sub.currency_id.id,
            "amount_tax": sub.amount_tax,
            "amount_total": sub.amount_total,
            "amount_tax_formatted": currency.format(sub.amount_tax),
            "amount_total_formatted": currency.format(sub.amount_total),
            "lines": [
                {
                    "name": line.product_id.product_tmpl_id.name,
                    "price_base": line.product_id.product_tmpl_id.list_price,
                    "price_base_formatted": currency.format(
                        line.product_id.product_tmpl_id.list_price
                    ),
                    "variant_values": [
                        {
                            "name": variant.attribute_id.name,
                            "value": variant.name,
                            "price_extra": variant.price_extra,
                            "price_extra_formatted": currency.format(
                                variant.price_extra
                            ),
                        }
                        for variant in line.product_id.product_template_variant_value_ids
                    ],
                    "stat_products": [
                        {
                            "name": stat_product.name,
                            "uom": stat_product.uom_id.name,
                            "price": stat_product.list_price,
                            "price_base_formatted": currency.format(
                                stat_product.list_price
                            ),
                        }
                        for stat_product in line.product_id.stat_product_ids
                    ],
                }
                for line in sub.sale_subscription_line_ids
            ],
        }

    @route(
        [
            """/application/order/<model("product.product","[('application_template_id', '!=', False), ('sale_ok', '=', True)]"):product>""",
            """/application/order""",
        ],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=True,
    )
    def order(self, product=False):
        main_product_tmpl = request.env["product.template"]
        if product:
            if not product.application_template_id or not product.sale_ok:
                return request.not_found()
            main_product_tmpl = product.product_tmpl_id
            optional_products = main_product_tmpl.optional_product_ids.filtered_domain(
                [("application_template_id", "!=", False), ("sale_ok", "=", True)]
            )
        else:
            optional_products = request.env["product.template"].search(
                [("application_template_id", "!=", False), ("sale_ok", "=", True)]
            )
        website = request.website.sudo()
        if "last_main_product_tmpl_id" in request.session:
            last_main_product_tmpl_id = request.session["last_main_product_tmpl_id"]
            if (
                last_main_product_tmpl_id
                and not main_product_tmpl
                or last_main_product_tmpl_id != main_product_tmpl.id
            ):
                website.reset_subscription()
        subscription = website.ensure_subscription()
        if main_product_tmpl and not subscription.sale_subscription_line_ids:
            website.update_subscription_product(
                main_product_tmpl.id,
                product.product_template_variant_value_ids.ids,
            )
        request.session["last_main_product_tmpl_id"] = (
            main_product_tmpl and main_product_tmpl.id or False
        )

        return request.render(
            "argocd_website.order",
            {
                "main_product_tmpl": main_product_tmpl,
                "optional_products": optional_products,
                "subscription": subscription,
                "current_step": "configure",
            },
        )

    @route(
        ["""/application/signup"""],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        sitemap=True,
    )
    def signup(self, **post):
        website = request.website.sudo()
        captcha_enabled = request.env["librecaptcha"].is_enabled()

        subscription = website.ensure_subscription()
        if not subscription.sale_subscription_line_ids:
            return request.redirect("/application/order")

        user = request.env.user
        user_is_public = user._is_public()
        render_values = {
            "subscription": subscription,
            "user": user,
            "user_is_public": user_is_public,  # Shortcut
            "user_is_reseller": user.partner_id.is_reseller,
            "captcha_enabled": captcha_enabled,
        }

        if request.httprequest.method == "POST":
            error = self._validate(
                post, captcha_enabled, user_is_public, user.partner_id.is_reseller
            )
            render_values.update(default=post, error=error)
            if error:
                return request.render("argocd_website.signup", render_values)

            # Prepare post data for the ORM
            if user_is_public or user.partner_id.is_reseller:
                values = {
                    "street": " ".join(
                        [
                            post["street_name"],
                            post["street_number"],
                            post["street_number2"],
                        ]
                    ),
                    "type": user_is_public and "invoice" or "other",
                    "company_type": "company",
                    "customer_rank": 1,
                    "lang": request.env.lang,
                    "name": post["name"],
                    "email": post["email"],
                    "company_registry": post["company_registry"],
                    "zip": post["zip"],
                    "city": post["city"],
                }

            if user_is_public:
                # Create user
                users_sudo = request.env["res.users"].sudo()
                signup_values = values.copy()
                signup_values.update(
                    login=post["email"], tz=request.httprequest.cookies.get("tz")
                )
                login = users_sudo.signup(signup_values)
                users_sudo.reset_password(post["email"])
                new_user = users_sudo.search([("login", "=", login)])
                env = api.Environment(
                    request.env.cr, new_user.id, request.session.context
                )
                request.session.pre_login = login
                request.session.pre_uid = new_user.id
                request.session.finalize(env)
                request.env = env
                request.update_context(**request.session.context)
                subscription.user_id = new_user
                subscription.partner_id = new_user.partner_id
            elif user.partner_id.is_reseller:
                # Create end customer
                reselling_partner = user.partner_id.parent_id or user.partner_id
                partner = request.env["res.partner"].sudo().create(values)
                partner.parent_id = reselling_partner

                subscription.partner_id = reselling_partner
                subscription.user_id = user
                subscription.end_partner_id = partner
            else:
                # Link subscription to current user
                subscription.partner_id = user.partner_id
                subscription.user_id = user

            if not subscription.invoice_ids:
                subscription.recurring_next_date = fields.Date.today()
                subscription.generate_invoice()
            subscription.invoice_ids.ensure_one()
            invoice_id = subscription.invoice_ids.id
            ctx = request.env.context.copy()
            ctx.update(
                {
                    "active_id": invoice_id,
                    "active_model": "account.move",
                }
            )
            link_wizard = (
                request.env["payment.link.wizard"].sudo().with_context(ctx).create({})
            )
            link_wizard._compute_link()
            return request.redirect(
                link_wizard.link
            )  # This will redirect to /payment/confirmation if the invoice has been paid

        return request.render("argocd_website.signup", render_values)
