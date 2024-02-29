from odoo import fields, models


class ApplicationValue(models.Model):
    """
    Simple key value pairs for argocd.application can be used for any generic value you
    want to take into account when generating the config (yaml).

    Use cases:
     * Custom domain names
     * Custom resource (cpu, memory, storage) allocation
    """

    _name = "argocd.application.value"
    _description = "Application Value"

    _sql_constraints = [
        ("application_key_unique", "UNIQUE(application_id, key)", "Key already in use")
    ]

    application_id = fields.Many2one(comodel_name="argocd.application", required=True)
    key = fields.Char(required=True)
    value = fields.Char()
