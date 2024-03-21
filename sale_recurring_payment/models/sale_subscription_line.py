from odoo import _, models
from odoo.exceptions import ValidationError


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    def create(self, vals):
        record = super().create(vals)
        if self.sale_subscription_id.payment_provider_subscription_id:
            raise ValidationError(
                _(
                    "New subscription line cannot be added for subscription with ongoing payment provider subscription"
                )
            )
        return record
