import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ApplicationNamespacePrefix(models.Model):
    _name = "argocd.application.namespace.prefix"
    _description = "Application Namespace Prefix"

    name = fields.Char(required=True)

    _sql_constraints = [
        ("application_namespace_name_prefix_unique", "unique(name)", "Already exists"),
        (
            "app_namespace_prefix_unique",
            "unique(name)",
            "A namespace prefix with that name was already defined.",
        ),
    ]

    @api.constrains("name")
    def _constrain_name(self):
        if not re.match(
            "^[a-z0-9-]{1,100}$", self.name
        ):  # lowercase a to z, 0 to 9 and - (dash) are allowed
            raise ValidationError(
                _(
                    "Only lowercase letters, numbers and dashes are allowed in the name (max 100 characters)."
                )
            )
