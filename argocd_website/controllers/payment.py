from odoo import _
from odoo.exceptions import ValidationError
from odoo.http import request, route

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers.portal import PaymentPortal


class ArgoCDPaymentPortal(PaymentPortal):
    @route(
        "/application/transaction/<int:subscription_id>",
        type="json",
        auth="public",
        website=True,
        sitemap=False,
    )
    def subscription_transaction(
        self,
        subscription_id,
        amount=None,
        access_token=None,
        **kwargs,
    ):
        self._validate_transaction_kwargs(kwargs)
        amount = self._cast_as_float(amount)
        if amount is None or kwargs.get("is_validation"):
            raise ValidationError(_("The subscription payment link is invalid."))

        partner = (
            False
            if request.env.user._is_public()
            else request.env.user.partner_id
        )
        subscription = self._get_subscription_for_payment(
            subscription_id,
            amount,
            partner.id if partner else False,
            access_token=access_token,
        )
        partner = (
            subscription.partner_id
            if request.env.user._is_public()
            else request.env.user.partner_id
        )
        kwargs.update(
            {
                "amount": amount,
                "currency_id": subscription.currency_id.id,
                "partner_id": partner.id,
                "reference_prefix": subscription.name,
            }
        )
        tx_sudo = self._create_transaction(
            custom_create_values={"subscription_id": subscription.id}, **kwargs
        )
        return tx_sudo._get_processing_values()

    def _get_extra_payment_form_values(self, subscription_id=None, **kwargs):
        res = super()._get_extra_payment_form_values(**kwargs)
        is_paying_for_app_subscription = bool(subscription_id)
        if "invoice_id" in kwargs:
            invoice = request.env["account.move"].sudo().browse(kwargs["invoice_id"])
            is_paying_for_app_subscription |= bool(
                invoice.line_ids.filtered(
                    lambda l: l.product_id.application_template_id
                )
            )
        res.update(is_paying_for_app_subscription=is_paying_for_app_subscription)
        if subscription_id:
            subscription = self._get_subscription_for_payment(
                subscription_id,
                kwargs.get("amount"),
                kwargs.get("partner_id"),
                kwargs.get("currency_id"),
                kwargs.get("access_token"),
            )
            res["transaction_route"] = (
                "/application/transaction/"
                f"{subscription.id}"
            )
        return res

    def _get_subscription_for_payment(
        self,
        subscription_id,
        amount,
        partner_id,
        currency_id=None,
        access_token=None,
    ):
        try:
            subscription_id = int(subscription_id)
        except (TypeError, ValueError):
            raise ValidationError(_("The subscription payment link is invalid."))

        # Sudo is needed to validate a public payment link against its subscription.
        subscription = (
            request.env["sale.subscription"].sudo().browse(subscription_id).exists()
        )
        partner = request.env["res.partner"].sudo().browse(partner_id).exists()
        if not partner and subscription:
            partner = subscription.partner_id
        currency_id = currency_id or (
            subscription.currency_id.id if subscription else False
        )
        if (
            not subscription
            or not partner
            or not subscription.website_id
            or (subscription.stage_id and subscription.stage_id.type != "draft")
            or subscription.invoice_ids
            or partner.commercial_partner_id
            != subscription.partner_id.commercial_partner_id
            or currency_id != subscription.currency_id.id
            or subscription.currency_id.compare_amounts(
                amount, subscription.amount_total
            )
            or not payment_utils.check_access_token(
                access_token,
                partner.id,
                amount,
                subscription.currency_id.id,
            )
        ):
            raise ValidationError(
                _("The subscription payment link is invalid or expired.")
            )

        # Public users cannot inspect transactions; only check for prior attempts.
        active_transaction = request.env["payment.transaction"].sudo().search(
            [
                ("subscription_id", "=", subscription.id),
                ("state", "in", ("pending", "authorized", "done")),
            ],
            limit=1,
        )
        if active_transaction:
            raise ValidationError(
                _("A payment for this subscription is already in progress.")
            )
        return subscription
