# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_subscription_line_values(self):
        res = super().get_subscription_line_values()
        if self.product_id.product_tmpl_id.membership_prorate:
            res["product_uom_qty"] = 1
        return res
