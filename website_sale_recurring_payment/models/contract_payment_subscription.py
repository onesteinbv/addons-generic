from odoo import fields, models


class ContractPaymentSubscription(models.Model):
    """The contract payment subscription is attached to a contract and represents a
    subscription that is created with payment providers to accept recurring
    payments for contracts
    """

    _name = "contract.payment.subscription"
    _description = "Contract Payment Subscription"
    _rec_name = "reference"

    reference = fields.Char(
        help="The reference of the subscription",
        readonly=True,
        required=True,
    )
    payment_transaction_ids = fields.One2many(
        "payment.transaction",
        "contract_payment_subscription_id",
        readonly=True,
    )
    provider_id = fields.Many2one(comodel_name="payment.provider", required=True)

    _sql_constraints = [
        ("reference_uniq", "unique(reference)", "Reference must be unique!"),
    ]
