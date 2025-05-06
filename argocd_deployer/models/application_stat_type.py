from odoo import fields, models


class ApplicationStatType(models.Model):
    _name = "argocd.application.stat.type"
    _description = "Application Statistic Type"

    _sql_constraints = [("key_uniq", "UNIQUE (key)", "Key must be unique.")]

    key = fields.Char(required=True)
    name = fields.Char(required=True)
