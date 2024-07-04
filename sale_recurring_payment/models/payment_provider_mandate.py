from odoo import fields, models


class PaymentProviderMandate(models.Model):
    """The payment provider mandate is attached to a sale subscription and represents a
    mandate that is created with payment providers to accept recurring
    payments for sale subscriptions
    """

    _name = "payment.provider.mandate"
    _description = "Payment Provider Mandate"
    _rec_name = "reference"

    reference = fields.Char(
        help="The reference of the mandate",
        readonly=True,
        required=True,
    )
    payment_transaction_ids = fields.One2many(
        "payment.transaction",
        "payment_provider_mandate_id",
        string="Payment Transactions",
        readonly=True,
    )
    provider_id = fields.Many2one(
        string="Provider", comodel_name="payment.provider", required=True
    )

    _sql_constraints = [
        ("reference_uniq", "unique(reference)", "Reference must be unique!"),
    ]
