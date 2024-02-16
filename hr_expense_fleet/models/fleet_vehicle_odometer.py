from odoo import api, fields, models


class FleetVehicleOdometer(models.Model):
    _inherit = "fleet.vehicle.odometer"

    partner_id = fields.Many2one("res.partner", "Contact Visited",
                                 help="Defines the contact visited for the trip if any")
    from_address = fields.Text("From", help="Defines the from address for the trip")
    to_address = fields.Text("To", help="Defines the to address for the trip")
    distance = fields.Float("Distance For Single Way Trip", help="Defines the distance covered for the trip")
    is_roundtrip = fields.Boolean("Is Roundtrip", help="Defines whether it is a round trip or not")
    total_distance = fields.Float("Total Distance", compute="_compute_total_distance",
                                  help="Defines the total distance covered including round trip")
    is_private_trip = fields.Boolean("Is Private Trip", help="Defines whether it is a private trip or not")
    value = fields.Float("Odometer End Value", group_operator="max", copy=False, )
    start_value = fields.Float("Odometer Start Value", group_operator="max", copy=False, )
    expense_id = fields.Many2one("hr.expense", "Expense", help="Defines expense record for this trip", copy=False)
    product_id = fields.Many2one("product.product", string="Expense Category",
                                 domain="[('can_be_expensed', '=', True),('can_be_used_for_fleet', '=', True)]",
                                 help="Defines expense category for this trip")
    status = fields.Selection(
        [("not_to_expense", "Not To Expense"), ("to_expense", "To Expense"), ("expense_created", "Expense Created")],
        "Status", help="Defines expense status for this trip", default="to_expense", copy=False)

    @api.depends("distance", "is_roundtrip")
    def _compute_total_distance(self):
        for rec in self:
            rec.total_distance = rec.distance * 2 if rec.is_roundtrip else rec.distance

    @api.onchange("is_private_trip")
    def _onchange_is_private_trip(self):
        if self.is_private_trip:
            self.status = "not_to_expense"
        else:
            self.status = "to_expense"

    @api.onchange("vehicle_id")
    def _onchange_vehicle(self):
        super()._onchange_vehicle()
        if self.vehicle_id:
            self.product_id = self.vehicle_id.product_id

    def action_create_expense(self):
        hr_expense_obj = self.env["hr.expense"]
        product_uom_km = self.env.ref("uom.product_uom_km")
        product_uom_mi = self.env.ref("uom.product_uom_mile")
        to_expense_odometers = self.filtered(lambda o: o.status == "to_expense" and (
                o.driver_employee_id == self.env.user.employee_id or not o.driver_employee_id))
        products = to_expense_odometers.mapped("product_id")
        for product in products:
            odometers = to_expense_odometers.filtered(lambda o: o.product_id == product)
            product_uom = product.uom_id
            if product_uom == product_uom_km:
                product_unit = "kilometers"
                odometer_uom_to_convert = product_uom_mi
            else:
                product_unit = "miles"
                odometer_uom_to_convert = product_uom_km
            total_distance = sum(
                line.total_distance for line in odometers.filtered(lambda ol: ol.unit == product_unit))
            for odometer in odometers.filtered(lambda ol: ol.unit != product_unit):
                total_distance += odometer_uom_to_convert._compute_quantity(odometer.total_distance, product_uom)
            ana_accounts = product.product_tmpl_id._get_product_analytic_accounts()
            ana_account = ana_accounts["expense"]
            hr_expense_rec = hr_expense_obj.create({
                "product_id": product.id,
                "quantity": total_distance,
                "analytic_distribution": (
                    {ana_account.id: 100} if ana_account else False
                )
            })
            odometers.write({"expense_id": hr_expense_rec.id, "status": "expense_created"})
        return True
