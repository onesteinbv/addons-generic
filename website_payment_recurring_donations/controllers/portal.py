# Copyright 2023 Onestein - Anjeel Haria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers import portal as payment_portal


class PaymentPortal(payment_portal.PaymentPortal):
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
        if request.env.user._is_public():
            kwargs["donation_partner_details"] = kwargs["partner_details"]
        return super().donation_transaction(
            amount, currency_id, partner_id, access_token, minimum_amount, **kwargs
        )

    def _get_custom_rendering_context_values(
        self,
        donation_options=None,
        donation_descriptions=None,
        is_donation=False,
        **kwargs
    ):
        rendering_context = super()._get_custom_rendering_context_values(
            donation_options=donation_options,
            donation_descriptions=donation_descriptions,
            is_donation=is_donation,
            **kwargs
        )
        if is_donation:
            if (
                kwargs.get("donation_frequency")
                and kwargs.get("donation_frequency") == "monthly"
            ):
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
        if kwargs.get("donation_frequency"):
            if not custom_create_values:
                custom_create_values = {}
            if (
                "donation_frequency" not in custom_create_values
            ):  # We are in the payment module's flow
                custom_create_values["donation_frequency"] = kwargs.pop(
                    "donation_frequency"
                )
            if kwargs.get("donation_partner_details"):
                res_partner_obj = request.env["res.partner"].sudo()
                details = kwargs.pop("donation_partner_details")
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
            **kwargs
        )
