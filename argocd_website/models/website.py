from odoo import api, models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    @api.returns("sale.subscription")
    def get_current_subscription(self, product_tmpl=False):
        """
        Get current draft subscription. Start a new when a different "main" product is selected.
        """
        self.ensure_one()
        subscription_sudo = self.env["sale.subscription"].sudo()
        subscription_id = request.session.get("subscription_id")
        if subscription_id:
            subscription_sudo = subscription_sudo.browse(subscription_id)
            if subscription_sudo.stage_id.type != "draft":
                subscription_sudo = self.env["sale.subscription"].sudo()

        user = request.env.user.id or request.website.user_id.id
        partner = user.partner_id

        if not subscription_sudo:
            subscription_sudo = subscription_sudo.create({"partner_id": partner.id})
            request.session["sale_order_id"] = subscription_sudo.id

        return subscription_sudo
