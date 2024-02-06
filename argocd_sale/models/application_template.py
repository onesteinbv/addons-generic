from odoo import fields, models


class ApplicationTemplate(models.Model):
    _inherit = "argocd.application.template"

    auto_send_deployment_notification = fields.Boolean(
        default=True,
        string="Automatically send deployment notification",
        help="Determines if an email is automatically send to the partner if deployed.",
    )
