from odoo import fields, models


class ApplicationTemplate(models.Model):
    _name = "argocd.application.template"
    _description = "ArgoCD Application Template"

    name = fields.Char(required=True)
    config = fields.Text()
    active = fields.Boolean(default=True)
