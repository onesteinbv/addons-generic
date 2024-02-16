from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    product_id = fields.Many2one("product.product", string="Expense Category",
                                 domain="[('can_be_expensed', '=', True),('can_be_used_for_fleet', '=', True)]",
                                 help="Defines default expense category for this vehicle's trips")
