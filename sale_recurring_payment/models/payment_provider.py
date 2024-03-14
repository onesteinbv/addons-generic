from odoo import api, fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    allows_recurring_payment = fields.Boolean()

    @api.model
    def _get_compatible_providers(self, *args, **kwargs):
        providers = super()._get_compatible_providers(*args, **kwargs)
        if kwargs.get("sale_order_id"):
            sale_order = self.env["sale.order"].sudo().browse(kwargs["sale_order_id"])
            if sale_order and sale_order.group_subscription_lines():
                providers = providers.filtered(lambda p: p.allows_recurring_payment)
        return providers
