from datetime import timedelta

from odoo import api, fields, models


class Subscription(models.Model):
    _inherit = "sale.subscription"

    template_id = fields.Many2one(
        default=lambda self: self._default_subscription_template_id()
    )
    website_id = fields.Many2one(comodel_name="website")
    application_transaction_ids = fields.One2many(
        comodel_name="payment.transaction",
        inverse_name="application_subscription_id",
    )
    has_confirmed_payment_not_in_progress = fields.Boolean(
        compute="_compute_has_confirmed_payment_not_in_progress",
        compute_sudo=True,
    )

    @api.depends("application_transaction_ids.state", "in_progress", "stage_id.type")
    def _compute_has_confirmed_payment_not_in_progress(self):
        for subscription in self:
            subscription.has_confirmed_payment_not_in_progress = (
                subscription.stage_id.type == "initial_payment"
                and not subscription.in_progress
                and any(
                    transaction.state == "done"
                    for transaction in subscription.application_transaction_ids
                )
            )

    def action_view_application_transactions(self):
        self.ensure_one()
        return {
            "name": self.env._("Payment Transactions"),
            "type": "ir.actions.act_window",
            "res_model": "payment.transaction",
            "view_mode": "list,form",
            "domain": [("application_subscription_id", "=", self.id)],
        }

    def _get_default_payment_link_values(self):
        self.ensure_one()
        return {
            "amount": self.amount_total,
            "amount_max": self.amount_total,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
        }

    def _default_subscription_template_id(self):
        website = self.env["website"].get_current_website()
        if not website:
            return False
        template_id = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_website.subscription_template_id", "0")
        )
        template = self.env["sale.subscription.template"].browse(template_id)
        return template

    def _cron_cleanup_abandoned(self):
        period = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_website.subscription_abandoned_period", "0")
        )
        if not period:
            return
        abandoned_date = fields.Datetime.now() - timedelta(days=period)
        abandoned_subscriptions = self.search(
            [
                ("website_id", "!=", False),
                ("create_date", "<=", fields.Datetime.to_string(abandoned_date)),
                "|",
                ("stage_id.type", "in", ["draft", "initial_payment"]),
                ("stage_id", "=", False),
            ]
        )
        abandoned_subscriptions.unlink()
