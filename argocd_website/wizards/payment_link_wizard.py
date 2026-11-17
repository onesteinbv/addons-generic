from odoo import models

from odoo.addons.payment import utils as payment_utils


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    def _prepare_subscription_access_token(self):
        self.ensure_one()
        subscription = self.env["sale.subscription"].browse(self.res_id)
        return payment_utils.generate_access_token(
            "argocd_subscription",
            subscription.id,
            subscription.partner_id.id,
            self.amount,
            self.currency_id.id,
            subscription._get_payment_checkout_signature(),
        )

    def _prepare_query_params(self, related_document):
        values = super()._prepare_query_params(related_document)
        if related_document._name != "sale.subscription":
            return values

        self.ensure_one()
        subscription = related_document
        values.update(
            {
                "subscription_id": subscription.id,
                "subscription_access_token": self._prepare_subscription_access_token(),
                
            }
        )
        return values
