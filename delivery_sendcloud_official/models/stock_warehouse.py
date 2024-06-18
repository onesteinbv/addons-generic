# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    sencloud_sender_address_id = fields.Many2one(
        related="partner_id.sencloud_sender_address_id", readonly=False
    )
