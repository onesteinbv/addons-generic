from odoo import api, fields, models


class PaymentProviderMandate(models.Model):
    """The payment provider mandate is attached to a sale subscription and represents a
    mandate that is created with payment providers to accept recurring
    payments for sale subscriptions
    """

    _name = "payment.provider.mandate"
    _description = "Payment Provider Mandate"

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
    payment_transaction_count = fields.Integer(
        compute="_compute_payment_transaction_count",
        store=True,
    )
    provider_id = fields.Many2one(
        string="Provider", comodel_name="payment.provider", required=True, readonly=True
    )
    is_revoked = fields.Boolean(
        help="If the mandate is revoked, no more payments can be made with this mandate",
        default=False,
        readonly=True,
    )
    partner_id = fields.Many2one(comodel_name="res.partner", readonly=True)

    _sql_constraints = [
        ("reference_uniq", "unique(reference)", "Reference must be unique!"),
    ]

    @api.depends("payment_transaction_ids")
    def _compute_payment_transaction_count(self):
        for record in self:
            record.payment_transaction_count = len(record.payment_transaction_ids)

    def revoke(self):
        self.is_revoked = True

    def name_get(self):
        res = []
        for record in self:
            res.append(
                (record.id, "%s (%s)" % (record.reference, record.provider_id.name))
            )
        return res
