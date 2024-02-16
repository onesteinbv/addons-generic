from odoo import api, fields, models


class Expense(models.Model):
    _inherit = "hr.expense"

    fleet_vehicle_odometer_ids = fields.One2many("fleet.vehicle.odometer", "expense_id", "OdoMeters", copy=False)
    odometer_count = fields.Integer(compute="_compute_odometer_count", string="Odometer")

    @api.depends("fleet_vehicle_odometer_ids")
    def _compute_odometer_count(self):
        for rec in self:
            rec.odometer_count = len(rec.fleet_vehicle_odometer_ids)

    def open_odometer(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Odometers",
            "res_model": "fleet.vehicle.odometer",
            "view_mode":"tree,kanban,form,graph",
            "domain": [("id", "in", self.fleet_vehicle_odometer_ids.ids)],
            "context": {"create": False, "edit": False},
        }
