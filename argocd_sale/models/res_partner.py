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
    is_reseller = fields.Boolean(compute="_compute_is_reseller")

    @api.depends("reselling_product_ids")
    def _compute_is_reseller(self):
        for partner in self:
            partner.is_reseller = bool(
                partner.company_type == "person"
                and partner.parent_id
                and partner.parent_id.reseller_product_ids
                or partner.reselling_product_ids
            )
