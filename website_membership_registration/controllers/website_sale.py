from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class MembershipRegistrationWebsiteSale(WebsiteSale):
    def _check_cart(self, order_sudo):
        res = super()._check_cart(order_sudo=order_sudo)
        if (
            order_sudo
            and order_sudo.order_line
            and order_sudo.order_line.mapped("product_id").filtered(
                lambda p: p.membership
            )
            and request.website.is_public_user()
        ):
            return request.redirect("/web/login?redirect=/shop/checkout")
        return res
