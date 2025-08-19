from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    first_of_period_billing_policy = fields.Boolean("Billing Policy: First of Period")

    @api.onchange("membership_type")
    def _onchange_membership_type(self):
        if not self.membership_type == "variable":
            self.subscribable = False
            self.subscription_template_id = False
