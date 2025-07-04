from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentPortal


class ArgocdPaymentPortal(PaymentPortal):
    def _get_extra_payment_form_values(self, **kwargs):
        res = super()._get_extra_payment_form_values(**kwargs)
        is_paying_for_app_subscription = False
        if "invoice_id" in kwargs:
            invoice = request.env["account.move"].sudo().browse(kwargs["invoice_id"])
            is_paying_for_app_subscription = bool(
                invoice.line_ids.filtered(
                    lambda l: l.product_id.application_template_id
                )
            )
        res.update(is_paying_for_app_subscription=is_paying_for_app_subscription)
        return res
