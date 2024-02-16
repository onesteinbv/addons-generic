from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.template"

    can_be_used_for_fleet = fields.Boolean("Can Be Used For Fleet",
                                           help="Helps to define whether this product is to be used for fleet or not")
    uom_id_domain = fields.Binary(string="UOM Domain",
                                  help="Dynamic domain used for the uom that can be set on product to be used for fleet",
                                  compute="_compute_uom_id_domain")

    @api.depends("can_be_used_for_fleet")
    def _compute_uom_id_domain(self):
        ids = [self.env.ref("uom.product_uom_km").id, self.env.ref("uom.product_uom_mile").id]
        for rec in self:
            rec.uom_id_domain = [("id", "in", ids)] if rec.can_be_used_for_fleet else []

    @api.onchange("can_be_used_for_fleet")
    def _onchange_can_be_used_for_fleet(self):
        if self.can_be_used_for_fleet:
            if self.uom_id not in [self.env.ref("uom.product_uom_km"), self.env.ref("uom.product_uom_mile")]:
                self.uom_id = self.env.ref("uom.product_uom_km").id
