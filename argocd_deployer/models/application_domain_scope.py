from odoo import fields, models


class DomainScope(models.Model):
    _name = "argocd.application.domain.scope"
    _description = "ArgoCD Application Domain Scope"

    name = fields.Char(required=True)

    _sql_constraints = [("name_unique", "unique(name)", "Scope name must be unique")]
