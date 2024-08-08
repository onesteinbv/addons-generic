from datetime import timedelta

from odoo import Command, _, fields, models


class Subscription(models.Model):
    _inherit = "sale.subscription"

    application_ids = fields.One2many(
        comodel_name="argocd.application", inverse_name="subscription_id"
    )
    end_partner_id = fields.Many2one(comodel_name="res.partner")
    application_count = fields.Integer(compute="_compute_application_count")

    def _compute_application_count(self):
        for sub in self:
            sub.application_count = len(sub.application_ids)

    def _get_grace_period(self):
        return int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_sale.grace_period", "0")
        )

    def _invoice_paid_hook(self):
        for subscription in self:
            # Start the subscription, which is not done by subscription_oca, so we do it here for our purposes
            # this probably should be moved to subscription_oca.
            if len(
                subscription.invoice_ids
            ) == 1 and subscription.sale_subscription_line_ids.filtered(
                lambda l: l.product_id.application_template_id
            ):
                subscription.action_start_subscription()

            lines = subscription.sale_subscription_line_ids.filtered(
                lambda l: l.product_id.application_template_id
            )
            for line in lines:
                line._invoice_paid_hook()

    def _do_grace_period_action(self):
        """
        Executes the grace period action on self.

        @return: False if nothing has been done, True if the action has been done
        """
        grace_period_action = self.env["ir.config_parameter"].get_param(
            "argocd_sale.grace_period_action"
        )
        if not grace_period_action:
            return False
        linked_apps = self.mapped("sale_subscription_line_ids.application_ids")
        if grace_period_action == "add_tag":
            grace_period_tag_id = int(
                self.env["ir.config_parameter"].get_param(
                    "argocd_sale.grace_period_tag_id", "0"
                )
            )
            if not grace_period_tag_id:
                return False
            tag = self.env["argocd.application.tag"].browse(grace_period_tag_id)
            if not tag:
                return False
            linked_apps.write({"tag_ids": [Command.link(tag.id)]})
        elif grace_period_action == "destroy_app":
            linked_apps.destroy()
        return True

    def cron_update_payment_provider_payments(self):
        # Process last payments first because in here paid_for_date can be updated
        res = super().cron_update_payment_provider_payments()
        period = self._get_grace_period()
        if not period:
            return res
        today = fields.Date.today()
        late_date = today - timedelta(days=period)
        late_subs = self.search(
            [("paid_for_date", "<", late_date), ("in_progress", "=", True)]
        )
        for late_sub in late_subs:
            late_sub.with_context(
                no_destroy_app=True
            ).close_subscription()  # no_destroy_app since we're doing the grace period action after this.
        late_subs._do_grace_period_action()
        return res

    def close_subscription(self, close_reason_id=False):
        if not self.env.context.get(
            "no_destroy_app", False
        ):  # This is fine since portal users don't have write access on sale.subscription and the super writes the record
            # Destroy app
            self.ensure_one()
            delta = self.recurring_next_date - fields.Date.today()
            for line in self.filtered(lambda l: l.application_ids):
                line.application_ids.destroy(eta=int(delta.total_seconds()))
        return super().close_subscription(close_reason_id)

    def view_applications(self):
        return {
            "name": _("Applications"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "argocd.application",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.application_ids.ids)],
        }
