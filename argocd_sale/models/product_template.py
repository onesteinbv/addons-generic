from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    application_template_id = fields.Many2one(
        string="Application Template", comodel_name="argocd.application.template"
    )

    application_tag_ids = fields.Many2many(
        comodel_name="argocd.application.tag",
        string="Application Tags",
    )

    application_filter_ids = fields.Many2many(
        comodel_name="argocd.application.template",
        string="Only applies to (leave empty for all)",
    )

    reseller_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="product_reseller_rel",
        string="Resellers",
        column1="product_template_id",
        column2="partner_id",
    )
