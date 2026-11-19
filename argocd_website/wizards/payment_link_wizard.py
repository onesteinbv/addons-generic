from odoo import models


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    def _prepare_query_params(self, related_document):
        res = super()._prepare_query_params(related_document)
        if self.res_model == "sale.subscription":
            res["application_subscription_id"] = related_document.id
            res["reference"] = related_document.name
        return res
