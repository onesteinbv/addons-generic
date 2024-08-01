from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    application_set_id = fields.Many2one(
        comodel_name="argocd.application.set",
        help="The application set in which this product will be deployed.",
    )

    application_template_id = fields.Many2one(
        string="Application Template", comodel_name="argocd.application.template"
    )

    application_tag_ids = fields.Many2many(
        comodel_name="argocd.application.tag",
        string="Application Tags",
    )

    reseller_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="product_reseller_rel",
        string="Resellers",
        column1="product_template_id",
        column2="partner_id",
    )

    allowed_reseller_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="product_reseller_all_rel",
        column1="product_template_id",
        column2="partner_id",
    )
