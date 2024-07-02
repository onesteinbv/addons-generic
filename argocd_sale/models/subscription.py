from datetime import timedelta

from odoo import Command, fields, models


class Subscription(models.Model):
    _inherit = "sale.subscription"

    application_ids = fields.One2many(
        comodel_name="argocd.application", inverse_name="subscription_id"
    )

    def _get_grace_period(self):
        return int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_sale.grace_period", "0")
        )

    def _invoice_paid_hook(self):
        for subscription in self.filtered(
            lambda i: len(i.invoice_ids) == 1
            and i.sale_subscription_line_ids.filtered(
                lambda l: l.product_id.application_template_id
            )
        ):  # Create the application after the first invoice has been paid
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
            return False  # Do nothing
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
            self.mapped("application_ids").write({"tag_ids": [Command.link(tag.id)]})
        elif grace_period_action == "destroy_app":
            self.mapped("application_ids").destroy()
        return True

    def cron_update_payment_provider_subscriptions(self):
        # Process last payments first because in here paid_for_date can be updated
        res = super().cron_update_payment_provider_subscriptions()
        period = self._get_grace_period()
        if not period:
            return res
        today = fields.Date.today()
        late_date = today - timedelta(days=period)
        late_subs = self.search(
            [("paid_for_date", "<", late_date), ("in_progress", "=", True)]
        )
        late_subs.close_subscription()
        late_subs._do_grace_period_action()
        return res
