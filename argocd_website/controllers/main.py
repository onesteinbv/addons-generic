import re

from odoo import Command, _
from odoo.exceptions import ValidationError
from odoo.http import Controller, request, route


class MainController(Controller):
    def _validate(self, post, captcha_enabled):
        if captcha_enabled:
            try:
                request.env["librecaptcha"].answer(
                    post["captcha_id"], post["captcha_answer"], raise_exception=True
                )
            except ValidationError as e:
                return {"subject": "captcha", "message": str(e)}

        if "terms_of_use" not in post:
            return {
                "subject": "terms_of_use",
                "message": _("Please accept the terms of use."),
            }
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
        if not post["coc"]:
            return {"subject": "coc", "message": _("CoC number is required.")}
        if not re.match(
            "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$",
            post["email"],
        ):
            return {"subject": "email", "message": _("Invalid email address.")}
        return False

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
            main_product_tmpl = product.product_tmpl_id.sudo()
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
        [
            """/application/additional/<model("product.product","[('application_template_id.active', '=', True), ('application_template_id', '!=', False)]"):product>"""
        ],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=True,
    )
    def additional(self, product):
        if (
            not product.application_template_id
            or not product.application_template_id.active
            or not product.sale_ok
        ):
            return request.not_found()

        additional_products = (
            request.env["product.product"]
            .search(
                [
                    ("application_tag_ids", "!=", False),
                    ("sale_ok", "=", True),
                    "|",
                    ("application_filter_ids", "=", False),
                    (
                        "application_filter_ids",
                        "in",
                        product.application_template_id.ids,
                    ),
                ]
            )
            .sudo()
        )
        if not additional_products:
            return request.redirect("/application/signup/%s" % product.id)
        return request.render(
            "argocd_website.additional",
            {
                "product": product,
                "additional_products": additional_products,
            },
        )

    @route(
        [
            """/application/signup/<model("product.product","[('application_template_id.active', '=', True), ('application_template_id', '!=', False)]"):product>"""
        ],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
        sitemap=True,
    )
    def form(self, product, **post):
        if (
            not product.application_template_id
            or not product.application_template_id.active
            or not product.sale_ok
        ):
            return request.not_found()

        error = False
        default = False
        captcha_enabled = request.env["librecaptcha"].is_enabled()

        # Check additional products
        additional_products = request.env["product.product"]
        for key in post:
            if not key.startswith("additional_product_"):
                continue
            additional_product_id = int(key.replace("additional_product_", ""))
            additional_product = request.env["product.product"].browse(
                additional_product_id
            )
            if (
                not additional_product.application_tag_ids
                or not additional_product.sale_ok
            ):  # Is not a additional modules product
                return request.not_found()  # TODO: Find a better response for this
            if (
                additional_product.application_filter_ids
                and product.application_template_id
                not in additional_product.application_filter_ids
            ):  # Is not suitable for this application (template)
                return request.not_found()  # TODO: Find a better response for this
            additional_products += additional_product

        if request.httprequest.method == "POST":
            error = self._validate(post, captcha_enabled)
            if not error:
                partner = (
                    request.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "company_type": "company",
                            "name": post["name"],
                            "type": "other",
                            "email": post["email"],
                            "street": " ".join(
                                [
                                    post["street_name"],
                                    post["street_number"],
                                    post["street_number2"],
                                ]
                            ),
                            "company_registry": post["coc"],
                            "zip": post["zip"],
                            "city": post["city"],
                            "customer_rank": 1,
                            "lang": "nl_NL",
                            "parent_id": request.env.user.partner_id.id,
                        }
                    )
                )
                subscription = (
                    request.env["sale.subscription"]
                    .sudo()
                    .create(
                        {
                            "partner_id": partner.id,
                            "sale_subscription_line_ids": [
                                Command.create({"product_id": product.id})
                            ]
                            + [
                                Command.create({"product_id": additional_product.id})
                                for additional_product in additional_products
                            ],
                            "pricelist_id": partner.property_product_pricelist.id,  # pricelist_id is done with an onchange in subscription_oca 👴
                        }
                    )
                )
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
                    request.env["payment.link.wizard"]
                    .sudo()
                    .with_context(ctx)
                    .create({})
                )
                link_wizard._compute_link()
                return request.redirect(link_wizard.link)
            default = post

        # Create query string for additional products
        additional_products_query = ""
        if additional_products:
            additional_products_query = "?"
            additional_products_query += "&".join(
                ["additional_product_%s=1" % p_id for p_id in additional_products.ids]
            )  # e.g. ?additional_product_12=1&additional_product_78=1

        return request.render(
            "argocd_website.form",
            {
                "currency": request.website.company_id.currency_id,
                "product": product,
                "additional_products": additional_products,
                "total": product.list_price
                + sum(additional_products.mapped("list_price")),
                "error": error,
                "default": default,
                "additional_products_query": additional_products_query,
                "captcha_enabled": captcha_enabled,
            },
        )
