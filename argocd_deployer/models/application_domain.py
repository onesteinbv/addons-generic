from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApplicationDomain(models.Model):
    _name = "argocd.application.domain"
    _description = "ArgoCD Application Domain"
    _order = "sequence"

    application_id = fields.Many2one(comodel_name="argocd.application", required=True)
    scope = fields.Char(default="Application", required=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    scope_unique = fields.Boolean(
        help="Whether the domain is unique within it's scope (true) or globally (false)"
    )
    url = fields.Boolean(
        default=True, help="Whether to display this domain as a link to the user"
    )

    @api.constrains("name", "scope", "scope_unique")
    def _constrain_name(self):
        domain = [("id", "!=", self.id), ("name", "=", self.name)]
        if self.scope_unique:
            domain += [("scope", "=", self.scope)]
        else:
            domain += [("scope_unique", "=", False)]
        if self.search_count(domain):
            raise ValidationError(_("Domain is already in use"))

    @api.model
    def create_domain(
        self,
        application,
        preferred,
        *alternatives,
        scope="Application",
        scope_unique=False,
        url=True
    ):
        existing = application.domain_ids.filtered(lambda d: d.scope == scope).sorted(
            "sequence"
        )
        if existing:
            return existing.name
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
                search_domain = [("name", "=", domain_name)]
                if scope_unique:
                    search_domain += [("scope", "=", scope)]
                else:
                    search_domain += [("scope_unique", "=", False)]

                already_exists = self.search_count(search_domain)
                if not already_exists:
                    best_available = domain_name
                    break
            i += 1
        self.create(
            {
                "application_id": application.id,
                "name": best_available,
                "scope": scope,
                "scope_unique": scope_unique,
                "url": url,
            }
        )
        return best_available
