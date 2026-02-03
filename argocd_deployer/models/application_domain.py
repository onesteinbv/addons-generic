from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApplicationDomain(models.Model):
    _name = "argocd.application.domain"
    _description = "ArgoCD Application Domain"
    _order = "sequence"

    application_id = fields.Many2one(comodel_name="argocd.application", required=True)
    scope_id = fields.Many2one(
        comodel_name="argocd.application.domain.scope", required=True
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    url = fields.Boolean(
        default=True, help="Whether to display this domain as a link to the user"
    )

    @api.constrains("name", "scope_id")
    def _constrain_name(self):
        domain = [
            ("id", "!=", self.id),
            ("name", "=", self.name),
            ("scope_id", "=", self.scope_id.id),
        ]
        if self.search_count(domain):
            raise ValidationError(_("Domain is already in use"))

    @api.model
    def create_domain(
        self, application, preferred, *alternatives, scope="Application", url=True
    ):
        # Find or create the domain scope
        domain_scope_model = self.env["argocd.application.domain.scope"]
        domain_scope = domain_scope_model.search([("name", "=", scope)])
        if not domain_scope:
            domain_scope = domain_scope_model.create({"name": scope})

        # Check if the application already has a domain in this scope
        existing = application.domain_ids.filtered(
            lambda d: d.scope_id == domain_scope
        ).sorted("sequence")
        if existing:
            return existing[0].name

        # Find the best available domain name
        domains = (preferred,) + alternatives
        i = 0
        best_available = False
        while not best_available:
            for domain in domains:
                domain_name = domain
                if i:
                    domain_levels = domain_name.split(".")
                    domain_levels[0] += str(i)
                    domain_name = ".".join(domain_levels)
                search_domain = [
                    ("name", "=", domain_name),
                    ("scope_id.name", "=", scope),
                ]

                already_exists = self.search_count(search_domain)
                if not already_exists:
                    best_available = domain_name
                    break
            i += 1
        self.create(
            {
                "application_id": application.id,
                "name": best_available,
                "scope_id": domain_scope.id,
                "url": url,
            }
        )
        return best_available
