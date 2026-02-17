from odoo import api, fields, models
from odoo.exceptions import UserError


class Application(models.Model):
    _inherit = "argocd.application"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_partner_id",
        store=True,
        readonly=False,
    )
    subscription_id = fields.Many2one(
        comodel_name="sale.subscription",
        compute="_compute_subscription_id",
        store=True,
        readonly=False,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        compute="_compute_product_id",
        store=True,
        readonly=False,
    )
    subscription_line_id = fields.Many2one(comodel_name="sale.subscription.line")

    _sql_constraints = [
        (
            "application_subscription_line_id_unique",
            "unique(subscription_line_id)",
            "Only one application can be linked to a subscription line",
        )
    ]

    def _get_config_render_values(self):
        res = super()._get_config_render_values()
        res["is_created_by_reseller"] = self.is_created_by_reseller
        res["get_attribute"] = self.get_attribute
        return res

    def is_created_by_reseller(self):
        self.ensure_one()
        partner = self.partner_id.parent_id or self.partner_id
        return partner.is_reseller or (
            partner.reseller_id and partner.reseller_id.is_reseller
        )

    def get_attribute(self, argocd_identifier):
        self.ensure_one()
        variant_value = self.product_id.product_template_variant_value_ids.filtered(
            lambda kv: kv.attribute_id.argocd_identifier == argocd_identifier
        ).product_attribute_value_id
        if not variant_value.argocd_value:
            raise UserError("No ArgoCD value found for attribute %s", argocd_identifier)
        return variant_value.argocd_value

    @api.depends("subscription_line_id", "subscription_line_id.sale_subscription_id")
    def _compute_subscription_id(self):
        for app in self.filtered(lambda a: a.subscription_line_id):
            app.subscription_id = app.subscription_line_id.sale_subscription_id

    @api.depends("subscription_line_id", "subscription_line_id.product_id")
    def _compute_product_id(self):
        for app in self.filtered(lambda a: a.subscription_line_id):
            app.product_id = app.subscription_line_id.product_id

    @api.depends(
        "subscription_id",
        "subscription_id.main_partner_id",
        "subscription_id.end_partner_id",
    )
    def _compute_partner_id(self):
        for app in self.filtered(lambda a: a.subscription_id):
            app.partner_id = (
                app.subscription_id.end_partner_id
                or app.subscription_id.main_partner_id  # We use the end partner if it exists, otherwise we fallback to the main partner NB: not commercial partner
            )
