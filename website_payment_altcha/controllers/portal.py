from odoo.addons.website_payment.controllers.portal import PaymentPortal


class PaymentPortalAltcha(PaymentPortal):
    @staticmethod
    def _validate_transaction_kwargs(kwargs, additional_allowed_keys=()):
        if isinstance(additional_allowed_keys, tuple):
            additional_allowed_keys += ("altcha",)
        elif isinstance(additional_allowed_keys, set):
            additional_allowed_keys.update(["altcha"])
        return super(
            PaymentPortalAltcha, PaymentPortalAltcha
        )._validate_transaction_kwargs(
            kwargs, additional_allowed_keys=additional_allowed_keys
        )
