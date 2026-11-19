from odoo import fields, models


class SubscriptionStage(models.Model):
    _inherit = "sale.subscription.stage"

    type = fields.Selection(
        selection_add=[("initial_payment", "Initial Payment")],
        ondelete={"initial_payment": "set default"},
    )
