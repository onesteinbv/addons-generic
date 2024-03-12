from odoo import fields, models


class PaymentProviderSubscription(models.Model):
    """The payment provider subscription is attached to a sale subscription and represents a
        subscription that is created with payment providers to accept recurring
        payments for sale subscriptions
        """

    _name = "payment.provider.subscription"
    _description = "Payment Provider Subscription"
    _rec_name = "reference"

    reference = fields.Char(
        string="Reference", help="The reference of the subscription", readonly=True,
        required=True)
    payment_transaction_ids = fields.One2many("payment.transaction",
                                              "payment_provider_subscription_id",
                                              string="Payment Transactions",
                                              readonly=True)
    provider_id = fields.Many2one(string="Provider", comodel_name='payment.provider', required=True)

    _sql_constraints = [
        ("reference_uniq", "unique(reference)", "Reference must be unique!"),
    ]
