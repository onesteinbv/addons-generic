from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers.portal import PaymentPortal


class ArgocdPaymentPortal(PaymentPortal):
    def _get_extra_payment_form_values(self, **kwargs):
        res = super()._get_extra_payment_form_values(**kwargs)
        application_subscription_id = kwargs.get("application_subscription_id")
        res.update(
            is_paying_for_app_subscription=bool(application_subscription_id),
        )
        if application_subscription_id:
            application_subscription_id = self._cast_as_int(application_subscription_id)
            if application_subscription_id:
                res["transaction_route"] = (
                    f"/application/transaction/{application_subscription_id}"
                )
        return res

    @http.route(
        "/application/transaction/<int:application_subscription_id>",
        type="json",
        auth="public",
        website=True,
        sitemap=False,
    )
    def application_transaction(
        self, application_subscription_id, amount, access_token, **kwargs
    ):
        amount = self._cast_as_float(amount)
        user = request.env.user
        subscription = (
            request.env["sale.subscription"]
            .sudo()
            .browse(application_subscription_id)
            .exists()
        )

        # Check if the subscription matches the expected parameters for this payment
        partner = user.partner_id
        if (
            user._is_public()
            or not subscription
            or subscription.website_id != request.website
            or subscription.user_id != user
            or subscription.stage_id.type != "draft"
            or subscription.partner_id.commercial_partner_id
            != partner.commercial_partner_id
            or subscription.currency_id.compare_amounts(
                amount, subscription.amount_total
            )
            != 0
        ):
            raise ValidationError(_("The payment parameters are invalid."))

        # Check that the payment token is valid for this partner, amount, and currency
        currency = subscription.currency_id
        if not payment_utils.check_access_token(
            access_token, partner.id, amount, currency.id
        ):
            raise ValidationError(_("The access token is invalid."))

        # Assert that no payment already exists
        if (
            request.env["payment.transaction"]
            .sudo()
            .search_count(
                [("application_subscription_id", "=", subscription.id)], limit=1
            )
        ):
            raise ValidationError(_("An initial payment was already attempted."))

        self._validate_transaction_kwargs(kwargs)

        # Update stage to initial payment to indicate that the initial payment process has started
        subscription.stage_id = request.env.ref(
            "argocd_website.subscription_stage_initial_payment"
        ).sudo()
        transaction = self._create_transaction(
            amount=amount,
            currency_id=currency.id,
            partner_id=partner.id,
            reference_prefix=subscription.name,
            custom_create_values={
                "application_subscription_id": subscription.id,
            },
            **kwargs,
        )
        self._update_landing_route(transaction, access_token)
        return transaction._get_processing_values()
