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
                sale_order = (
                    request.env["sale.order"]
                    .sudo()
                    .create(
                        {
                            "partner_id": partner.id,
                            "order_line": [Command.create({"product_id": product.id})]
                            + [
                                Command.create({"product_id": additional_product.id})
                                for additional_product in additional_products
                            ],
                        }
                    )
                )
                sale_order.action_confirm()
                if sale_order.amount_total == 0:
                    sale_order._create_invoices()
                    sale_order.invoice_ids.action_post()

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
