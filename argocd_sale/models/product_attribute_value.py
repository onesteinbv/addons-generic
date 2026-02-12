from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    argocd_value = fields.Char(string="Value in ArgoCD")
