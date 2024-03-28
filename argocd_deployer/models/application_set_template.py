from odoo import fields, models


class ApplicationSetTemplate(models.Model):
    _name = "argocd.application.set.template"
    _description = "ArgoCD Application Set Template"

    name = fields.Char(required=True)
    yaml = fields.Text(
        default="""
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name:
  namespace:
spec:
  """
    )
    active = fields.Boolean(default=True)
