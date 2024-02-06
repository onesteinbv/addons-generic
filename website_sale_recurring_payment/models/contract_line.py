from odoo import _, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    _inherit = "contract.line"

    def create(self, vals):
        record = super().create(vals)
        if self.contract_id.contract_payment_subscription_id:
            raise ValidationError(
                _(
                    "New contract line cannot be added for contract with ongoing provider subscription"
                )
            )
        return record
