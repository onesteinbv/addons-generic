from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    allows_recurring_payment = fields.Boolean()
