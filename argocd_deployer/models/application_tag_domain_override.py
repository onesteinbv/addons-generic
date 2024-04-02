from odoo import fields, models


class ApplicationTagDomainOverride(models.Model):
    _name = "argocd.application.tag.domain.override"
    _description = "Application Tag Domain Override"

    tag_id = fields.Many2one("argocd.application.tag")
    application_set_id = fields.Many2one("argocd.application.set")
    domain_yaml_path = fields.Char(
        help="Path where to find the domain in the yaml (e.g. nextcloud.domain)"
    )

    _sql_constraints = [
        (
            "application_tag_key_unique",
            "unique(tag_id, application_set_id)",
            "Override already exists.",
        )
    ]
