# Copyright 2023 Onestein - Anjeel Haria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentPortal as payment_portal


class PaymentPortal(payment_portal):
    @http.route(
        "/donation/transaction/<minimum_amount>",
        type="json",
        auth="public",
        website=True,
        sitemap=False,
    )
    def donation_transaction(
        self, amount, currency_id, partner_id, access_token, minimum_amount=0, **kwargs
    ):
        donation_frequency = kwargs.pop("donation_frequency", False)
        context = request.env.context.copy()
        context.update({"donation_frequency": donation_frequency})
        if request.env.user._is_public():
            context.update({"donation_partner_details": kwargs["partner_details"]})
        request.env.context = context
        return super().donation_transaction(
            amount, currency_id, partner_id, access_token, minimum_amount, **kwargs
        )

    def _get_extra_payment_form_values(
        self,
        donation_options=None,
        donation_descriptions=None,
        is_donation=False,
        **kwargs,
    ):
        donation_frequency = kwargs.pop("donation_frequency", False)
        if donation_frequency:
            kwargs["custom_create_values"] = {"donation_frequency": donation_frequency}
        rendering_context = super()._get_extra_payment_form_values(
            donation_options=donation_options,
            donation_descriptions=donation_descriptions,
            is_donation=is_donation,
            **kwargs,
        )
        if is_donation:
            if donation_frequency and donation_frequency == "monthly":
                is_monthly = True
            else:
                is_monthly = False
            rendering_context.update(
                {
                    "is_onetime": not is_monthly,
                    "is_monthly": is_monthly,
                }
            )
        return rendering_context

    def _create_transaction(
        self, partner_id, *args, custom_create_values=None, **kwargs
    ):
        if "donation_frequency" in request.env.context and request.env.context.get(
            "donation_frequency"
        ):
            if not custom_create_values:
                custom_create_values = {}
            if (
                "donation_frequency" not in custom_create_values
            ):  # We are in the payment module's flow
                custom_create_values["donation_frequency"] = request.env.context.get(
                    "donation_frequency"
                )
            if request.env.context.get("donation_partner_details", False):
                res_partner_obj = request.env["res.partner"].sudo()
                details = request.env.context.get("donation_partner_details")
                country_id = int(details.get("country_id"))
                email = details.get("email")
                partner_id = res_partner_obj.search(
                    [("email", "=ilike", email), ("country_id", "=", country_id)],
                    limit=1,
                ).id
                if not partner_id:
                    partner_id = res_partner_obj.create(
                        {
                            "name": details.get("name"),
                            "email": email,
                            "country_id": country_id,
                        }
                    ).id
        return super()._create_transaction(
            partner_id=partner_id,
            *args,
            custom_create_values=custom_create_values,
            **kwargs,
        )
