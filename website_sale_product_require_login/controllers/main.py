from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class MainController(WebsiteSale):
    def _require_login(self):
        return (
            request.website.website_sale_product_require_login
            and request.website.is_public_user()
        )

    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        if self._require_login():
            return request.redirect("/web/login")
        return super().shop(page, category, search, ppg, **post)

    @http.route()
    def product(self, product, category="", search="", **kwargs):
        if self._require_login():
            return request.redirect("/web/login")
        return super().product(product, category, search, **kwargs)

    @http.route()
    def pricelist(self, promo, **post):
        if self._require_login():
            return request.redirect("/web/login")
        return super().pricelist(promo, **post)

    @http.route()
    def cart(self, **post):
        if self._require_login():
            return request.redirect("/web/login")
        return super().cart(**post)

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        if self._require_login():
            return request.redirect("/web/login")
        return super().cart_update(product_id, add_qty, set_qty, **kw)

    @http.route()
    def address(self, **kw):
        if self._require_login():
            return request.redirect("/web/login")
        return super().address(**kw)

    @http.route()
    def checkout(self, **post):
        if self._require_login():
            return request.redirect("/web/login")
        return super().checkout(**post)

    @http.route()
    def confirm_order(self, **post):
        if self._require_login():
            return request.redirect("/web/login")
        return super().confirm_order(**post)

    @http.route()
    def extra_info(self, **post):
        if self._require_login():
            return request.redirect("/web/login")
        return super().extra_info(**post)

    @http.route()
    def print_saleorder(self, **kwargs):
        if self._require_login():
            return request.redirect("/web/login")
        return super().print_saleorder(**kwargs)
