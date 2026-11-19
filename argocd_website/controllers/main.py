import re
from urllib.parse import urlencode

from odoo import _, api, fields
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing


class MainController(Controller):
    def _get_pending_application_transaction(self):
        user = request.env.user
        transaction_id = request.session.get(PaymentPostProcessing.MONITORED_TX_ID_KEY)
        transaction = (
            request.env["payment.transaction"].sudo().browse(transaction_id).exists()
        )
        if (
            not transaction
            or transaction.state not in ("draft", "pending", "authorized")
            or not transaction.application_subscription_id
            or (
                not user._is_public()
                and transaction.application_subscription_id.user_id != user
            )
            or transaction.application_subscription_id.website_id != request.website
            or transaction.application_subscription_id.stage_id.type
            != "initial_payment"
        ):
            return request.env["payment.transaction"]
        return transaction

    def _validate(self, post, captcha_enabled, is_public, reselling_partner):
        if captcha_enabled:
            try:
                request.env["librecaptcha"].answer(
                    post["captcha_id"], post["captcha_answer"], raise_exception=True
                )
            except ValidationError as e:
                return {"subject": "captcha", "message": str(e)}

        if is_public:
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

            existing_users = (
                request.env["res.users"]
                .sudo()
                .search_count([("login", "=", post["email"])])
            )
            if existing_users:
                return {
                    "subject": "email",
                    "message": _("Email address already in use."),
                }

        # Validate reseller selections
        if reselling_partner:
            customer_id = post.get("customer_id", False)
            target = post.get("target", "self")

            # customer_id is required if target is end_customer
            if target == "end_customer" and not customer_id:
                return {
                    "subject": "customer_id",
                    "message": _("Please select a customer."),
                }

            # Check whether the selected customer belongs to the reseller if target is end_customer
            if target == "end_customer" and customer_id:
                # Ensure the selected customer belongs to the reseller
                partner = request.env["res.partner"].browse(int(customer_id))

                # This is already ensured by the record rule
                if partner.reseller_id != reselling_partner:
                    return {
                        "subject": "customer_id",
                        "message": _("Invalid customer selection."),
                    }

        if "terms_of_use" not in post:
            return {
                "subject": "terms_of_use",
                "message": _("Please accept the terms of use."),
            }

        return False

    @route(
        "/application/update_subscription_product",
        type="json",
        auth="public",
        website=True,
    )
    def update_subscription_product(self, product_template_id, combination):
        request.env["product.template"].browse(product_template_id).check_access("read")
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
        res = {
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
        return res

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
    def order(self, product=False, customer_id=None):
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
                "customer_id": customer_id,
                "pending_application_transaction": (
                    self._get_pending_application_transaction()
                ),
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
        # captcha_enabled = request.env["librecaptcha"].is_enabled()
        captcha_enabled = False

        subscription = website.ensure_subscription()
        if not subscription.sale_subscription_line_ids:
            return request.redirect("/application/order")

        user = request.env.user
        user_is_public = user._is_public()
        is_reseller = user.partner_id.is_reseller or (
            user.partner_id.parent_id and user.partner_id.parent_id.is_reseller
        )

        # Fetch existing customers for resellers
        existing_customers = request.env["res.partner"]
        customer_id = post.get("customer_id", False)
        if is_reseller:
            reselling_partner = user.partner_id.parent_id or user.partner_id
            existing_customers = request.env["res.partner"].search(
                [("reseller_id", "=", reselling_partner.id)]
            )

        render_values = {
            "subscription": subscription,
            "user": user,
            "user_is_public": user_is_public,  # Shortcut
            "user_is_reseller": is_reseller,
            "captcha_enabled": captcha_enabled,
            "existing_customers": existing_customers,
            "customer_id": customer_id,
            "target": post.get("target", "end_customer" if customer_id else "self"),
            "pending_application_transaction": (
                self._get_pending_application_transaction()
            ),
        }

        if request.httprequest.method == "POST":
            if error := self._validate(
                post,
                captcha_enabled,
                user_is_public,
                reselling_partner if is_reseller else False,
            ):
                render_values.update(default=post, error=error)
                return request.render("argocd_website.signup", render_values)

            # Prepare post data for the ORM
            if user_is_public:
                values = {
                    "street": " ".join(
                        [
                            post["street_name"],
                            post["street_number"],
                            post["street_number2"],
                        ]
                    ),
                    "company_type": "company",
                    "customer_rank": 1,
                    "lang": request.env.lang,
                    "name": post["name"],
                    "email": post["email"],
                    "company_registry": post["company_registry"],
                    "zip": post["zip"],
                    "city": post["city"],
                }
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
            elif is_reseller:
                reselling_partner = user.partner_id.parent_id or user.partner_id
                subscription.user_id = user
                target = post.get("target", "self")
                if target == "self":  # Reseller ordering for their own company
                    subscription.partner_id = reselling_partner
                elif target == "end_customer" and customer_id:
                    subscription.partner_id = reselling_partner
                    subscription.end_partner_id = request.env["res.partner"].browse(
                        int(customer_id)
                    )
            else:
                # Link subscription to current user
                subscription.partner_id = user.partner_id
                subscription.user_id = user

            subscription.recurring_next_date = fields.Date.today()
            subscription.stage_id = request.env.ref(
                "argocd_website.subscription_stage_initial_payment"
            ).sudo()
            partner = request.env.user.partner_id
            currency = subscription.currency_id
            payment_url = "/payment/pay?" + urlencode(
                {
                    "amount": subscription.amount_total,
                    "currency_id": currency.id,
                    "partner_id": partner.id,
                    "company_id": subscription.company_id.id,
                    "reference": subscription.name,
                    "access_token": payment_utils.generate_access_token(
                        partner.id, subscription.amount_total, currency.id
                    ),
                    "application_subscription_id": subscription.id,
                }
            )
            return request.redirect(payment_url)

        return request.render("argocd_website.signup", render_values)
