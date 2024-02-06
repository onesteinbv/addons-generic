from odoo import api, fields, models

from odoo.addons.queue_job.exception import RetryableJobError


class Application(models.Model):
    _inherit = "argocd.application"

    volume_claim_count = fields.Integer(
        string="Estimated Volume Claims",
        compute="_compute_volume_claim_count",
        store=True,
    )

    capacity_reached = fields.Boolean(compute="_compute_capacity_reached")

    @api.depends("tag_ids.volume_claim_count", "template_id.volume_claim_count")
    def _compute_volume_claim_count(self):
        for app in self:
            app.volume_claim_count = app.template_id.volume_claim_count + sum(
                app.tag_ids.mapped("volume_claim_count")
            )

    @api.depends("volume_claim_count")
    def _compute_capacity_reached(self):
        capacity_reached = self.has_capacity_reached()
        for app in self:
            app.capacity_reached = capacity_reached

    @api.model
    def has_capacity_reached(self):
        volume_claim_capacity = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_capacity.volume_claim_capacity", "0")
        )
        if volume_claim_capacity <= 0:
            return False
        return sum(self.search([]).mapped("volume_claim_count")) > volume_claim_capacity

    def _get_deployment_notification_mail_template(self):
        return (
            self.has_capacity_reached()
            and "argocd_capacity.deployment_delayed_notification_mail_template"
            or super()._get_deployment_notification_mail_template()
        )

    def immediate_deploy(self):
        self.ensure_one()
        if self.has_capacity_reached():  # Make sure it's not orm cached computed
            raise RetryableJobError(
                "Servers capacity reached delaying this deployment (retry in 1 hour)",
                seconds=3600,
                ignore_retry=True,
            )
        return super().immediate_deploy()
