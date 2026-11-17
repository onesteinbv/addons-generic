from odoo import models


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    def _prepare_query_params(self, related_document):
        values = super()._prepare_query_params(related_document)
        if related_document._name != "sale.subscription":
            return values

        self.ensure_one()
        subscription = related_document
        values["subscription_id"] = subscription.id
        return values
