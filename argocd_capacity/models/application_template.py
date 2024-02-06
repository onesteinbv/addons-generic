from odoo import fields, models


class ApplicationTemplate(models.Model):
    _inherit = "argocd.application.template"

    volume_claim_count = fields.Integer(string="Estimated Volume Claims")
