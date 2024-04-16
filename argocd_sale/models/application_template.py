from odoo import fields, models


class ApplicationTemplate(models.Model):
    _inherit = "argocd.application.template"

    send_deployment_mail = fields.Boolean(
        default=True,
        string="Send Deployment Email",
        help="Send an email when deployment is invoked",
    )
