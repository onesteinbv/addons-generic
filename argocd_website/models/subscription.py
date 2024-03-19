from odoo import fields, models


class Subscription(models.Model):
    _inherit = "sale.subscription"

    template_id = fields.Many2one(
        default=lambda self: self._default_subscription_template_id()
    )

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

    def _stop_service_hook(self):
        res = super()._stop_service_hook()
        apps_to_destroy = self.env["argocd.application"].search(
            [("subscription_id", "=", self.id)]
        )
        for app in apps_to_destroy:
            app.destroy()
        return res
