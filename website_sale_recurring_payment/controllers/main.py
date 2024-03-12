from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        """
        show only payment methods who allow for recurring payment, if the order is a subscription
        """
        values = super(WebsiteSale, self)._get_shop_payment_values(order, **kwargs)
        if order:
            if order.group_subscription_lines():
                values['providers'] = values['providers'].filtered(lambda x: x.allows_recurring_payment)
        return values
