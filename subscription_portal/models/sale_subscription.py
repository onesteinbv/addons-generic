from odoo import models


class SaleSubscription(models.Model):
    _name = "sale.subscription"
    _inherit = [
        "sale.subscription",
        "portal.mixin",
    ]

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/subscriptions/{}".format(record.id)
