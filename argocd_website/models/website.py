from odoo import Command, api, models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def reset_subscription(self):
        subscription = self.ensure_subscription()
        subscription.sale_subscription_line_ids = [Command.clear()]

    def update_subscription_product(self, product_id):
        product = self.env["product.product"].browse(product_id)
        subscription = self.ensure_subscription()
        existing_line = subscription.sale_subscription_line_ids.filtered(
            lambda l: l.product_id.product_tmpl_id == product.product_tmpl_id
        )
        if not existing_line:
            subscription.sale_subscription_line_ids = [
                Command.create({"product_id": product.id})
            ]
        else:
            existing_line.product_id = product

    def remove_subscription_product(self, product_template_id):
        subscription = self.ensure_subscription()
        to_remove = subscription.sale_subscription_line_ids.filtered(
            lambda l: l.product_id.product_tmpl_id.id == product_template_id
        )
        subscription.sale_subscription_line_ids = [
            Command.unlink(t.id) for t in to_remove
        ]

    @api.returns("sale.subscription")
    def ensure_subscription(self):
        """
        Get current draft subscription. The draft subscription is like a shopping cart but for a subscription
        """
        self.ensure_one()
        subscription = self.env["sale.subscription"]
        subscription_id = request.session.get(
            "subscription_id"
        )  # Session is retrieved by cookie, so we don't need to filter on website
        if subscription_id:
            subscription = subscription.browse(subscription_id)
            if not subscription.exists() or (
                subscription.stage_id and subscription.stage_id.type != "draft"
            ):
                subscription = self.env["sale.subscription"]

        user = request.env.user or self.user_id
        partner = user.partner_id.commercial_partner_id

        if not subscription:
            draft_stage = self.env["sale.subscription.stage"].search(
                [("type", "=", "draft")], order="sequence desc", limit=1
            )
            subscription = subscription.create(
                {
                    "partner_id": partner.id,
                    "website_id": self.id,
                    "pricelist_id": partner.property_product_pricelist.id,
                    "stage_id": draft_stage and draft_stage.id,
                }
            )
            request.session["subscription_id"] = subscription.id
        else:
            subscription.partner_id = partner
        subscription.onchange_partner_id()
        subscription.onchange_partner_id_fpos()

        return subscription
