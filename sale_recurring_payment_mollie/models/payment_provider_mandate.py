from odoo import models


class PaymentProviderMandate(models.Model):
    _inherit = "payment.provider.mandate"

    def revoke(self):
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_mandates = self.filtered(lambda m: m.provider_id == mollie)
        if mollie_mandates:
            mollie_client = mollie._api_mollie_get_client()

        for mandate in mollie_mandates:
            customer = mollie_client.customers.get(
                mandate.partner_id.mollie_customer_id
            )
            customer.mandates.delete(mandate.reference)

        return super().revoke()
