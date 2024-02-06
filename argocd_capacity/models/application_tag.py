from odoo import fields, models


class ApplicationTag(models.Model):
    _inherit = "argocd.application.tag"

    volume_claim_count = fields.Integer(string="Estimated Volume Claims")
