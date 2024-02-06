from odoo import fields, models


class ApplicationTemplate(models.Model):
    _name = "argocd.application.template"
    _description = "ArgoCD Application Template"

    name = fields.Char(required=True)
    config = fields.Text(
        default="""helm: |
  domain: dev.curq.k8s.onestein.eu
  modules: website{{ application.modules and ',' + application.modules or '' }}
"""
    )
    active = fields.Boolean(default=True)
