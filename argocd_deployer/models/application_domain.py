from odoo import api, fields, models


class ApplicationDomain(models.Model):
    _name = "argocd.application.domain"
    _description = "ArgoCD Application Domain"
    _order = "sequence"

    application_id = fields.Many2one(comodel_name="argocd.application", required=True)
    scope = fields.Char(default="Application")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)

    _sql_constraints = [
        (
            "application_domain_name_unique",
            "unique(name)",
            "Domain is already in use",
        )
    ]

    @api.model
    def create_domain(self, application, preferred, *alternatives, scope="Application"):
        existing = application.domain_ids.filtered(lambda d: d.scope == scope).sorted(
            "sequence"
        )
        if existing:
            return existing.name
        domains = (preferred,) + alternatives
        i = 0
        best_available = False
        while not best_available:
            i_as_str = str(i)
            for domain in domains:
                domain_name = domain
                if i:
                    domain_name += i_as_str
                already_exists = self.search([("name", "=", domain_name)], count=True)
                if not already_exists:
                    best_available = domain_name
                    break
            i += 1
        self.create(
            {"application_id": application.id, "name": best_available, "scope": scope}
        )
        return best_available
