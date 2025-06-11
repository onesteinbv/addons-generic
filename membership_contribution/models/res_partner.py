from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    membership_subscription_contribution = fields.Float(
        compute="_compute_membership_contribution", store=True
    )
    membership_total_contribution = fields.Float(
        compute="_compute_membership_contribution", store=True
    )
    membership_contribution_currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    @api.depends(
        "member_lines",
        "membership_contribution_currency_id",
        "member_lines.account_invoice_line",
        "member_lines.account_invoice_id.state",
        "member_lines.account_invoice_id.payment_state",
    )
    def _compute_membership_contribution(self):
        for partner in self:
            currency = partner.membership_contribution_currency_id
            membership_subscription_contribution = 0
            for membership in partner.member_lines.filtered(
                lambda x: x.state == "paid"
            ):
                membership_subscription_contribution += currency._convert(
                    membership.account_invoice_line.price_total,
                    membership.account_invoice_id.currency_id,
                    partner.company_id or self.env.company,
                    membership.account_invoice_id.invoice_date or fields.Date.today(),
                )

            partner.membership_subscription_contribution = (
                membership_subscription_contribution
            )
            partner.membership_total_contribution = membership_subscription_contribution
