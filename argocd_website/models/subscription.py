from datetime import timedelta

from odoo import fields, models


class Subscription(models.Model):
    _inherit = "sale.subscription"

    template_id = fields.Many2one(
        default=lambda self: self._default_subscription_template_id()
    )
    website_id = fields.Many2one(comodel_name="website")

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
            .get_param("argocd_website.subscription_abandoned_period" "0")
        )
        if not period:
            return
        abandoned_date = fields.Datetime.now() - timedelta(days=period)
        self.search(
            [
                (
                    "website_id",
                    "!=",
                    False,
                    "create_date",
                    "<=",
                    fields.Datetime.to_string(abandoned_date),
                    "|",
                    "stage_id.type",
                    "=",
                    "draft",
                    "stage_id",
                    "=",
                    False,
                )
            ]
        ).unlink()
