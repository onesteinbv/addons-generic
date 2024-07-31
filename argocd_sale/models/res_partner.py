from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    reselling_product_ids = fields.Many2many(
        comodel_name="product.template",
        relation="product_reseller_rel",
        string="Reselling Products",
        column1="partner_id",
        column2="product_template_id",
    )
    allowed_reselling_products_ids = fields.Many2many(
        comodel_name="product.template",
        compute="_compute_allowed_reselling_products_ids",
        store=True,
    )
    is_reseller = fields.Boolean(compute="_compute_is_reseller")

    @api.depends(
        "reselling_product_ids", "parent_id", "parent_id.reselling_product_ids"
    )
    def _compute_allowed_reselling_products_ids(self):
        for partner in self:
            allowed_reselling_products_ids = partner.reselling_product_ids
            if partner.parent_id:
                allowed_reselling_products_ids += (
                    partner.parent_id.reselling_product_ids
                )
            partner.allowed_reselling_products_ids = allowed_reselling_products_ids

    @api.depends("allowed_reselling_products_ids")
    def _compute_is_reseller(self):
        for partner in self:
            partner.is_reseller = bool(partner.allowed_reselling_products_ids)
