from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    argocd_identifier = fields.Char(
        string="ArgoCD Identifier",
        help="Makes it easier to look it up when rendering the YAML config for applications",
    )
