from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    application_set_id = fields.Many2one(
        comodel_name="argocd.application.set",
        help="The application set in which this product will be deployed.",
    )

    application_template_id = fields.Many2one(
        string="Application Template", comodel_name="argocd.application.template"
    )

    reseller_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="product_reseller_rel",
        string="Resellers",
        column1="product_template_id",
        column2="partner_id",
        domain="[('is_reseller', '=', True)]",
        help="Resellers allowed to sell this product. If no reseller is added, it's a public product.",
    )

    application_stat_type_id = fields.Many2one(
        string="Statistics Type", comodel_name="argocd.application.stat.type"
    )
    stat_threshold = fields.Float(string="Statistics Threshold")
    stat_product_ids = fields.Many2many(
        comodel_name="product.product", string="Products on Statistics"
    )

    @api.constrains("application_template_id", "application_set_id")
    def _constrain_application_template(self):
        """Ensure that if an application template is set, an application set is also set."""
        for record in self:
            if record.application_template_id and not record.application_set_id:
                raise ValidationError(
                    "An application set must be set if an application template is set."
                )
            elif record.application_set_id and not record.application_template_id:
                raise ValidationError(
                    "An application template must be set if an application set is set."
                )
