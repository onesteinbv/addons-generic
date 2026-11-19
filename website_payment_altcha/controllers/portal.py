from odoo.addons.website_payment.controllers.portal import PaymentPortal


class PaymentPortalAltcha(PaymentPortal):
    @classmethod
    def _validate_transaction_kwargs(cls, kwargs, additional_allowed_keys=()):
        additional_allowed_keys = tuple(additional_allowed_keys) + ("altcha",)
        return super()._validate_transaction_kwargs(
            kwargs, additional_allowed_keys=additional_allowed_keys
        )
