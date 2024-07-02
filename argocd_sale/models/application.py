from odoo import api, fields, models


class Application(models.Model):
    _inherit = "argocd.application"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_partner_id",
        store=True,
        readonly=False,
    )
    subscription_id = fields.Many2one(
        comodel_name="sale.subscription", compute="_compute_subscription_id"
    )
    subscription_line_id = fields.Many2one(comodel_name="sale.subscription")

    _sql_constraints = [
        (
            "application_subscription_line_id_unique",
            "unique(subscription_line_id)",
            "Only one application can be linked to a subscription line",
        )
    ]

    def is_created_by_reseller(self):
        self.ensure_one()
        return self.partner_id.is_reseller or (
            self.partner_id.parent_id and self.partner_id.parent_id.is_reseller
        )

    @api.depends("subscription_line_id", "subscription_line_id.sale_subscription_id")
    def _compute_subscription_id(self):
        for app in self.filtered(lambda a: a.subscription_line_id):
            app.subscription_id = app.subscription_line_id.sale_subscription_id

    @api.depends("subscription_id", "subscription_id.partner_id")
    def _compute_partner_id(self):
        for app in self.filtered(lambda a: a.subscription_id):
            app.partner_id = app.subscription_id.partner_id
