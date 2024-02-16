# -*- coding: utf-8 -*-
from odoo.tests import common


class TestHrExpenseFleet(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_mileage = cls.env.ref("hr_expense.expense_product_mileage")
        cls.product_expense = cls.env["product.product"].create({
            "name": "Travel",
            "default_code": "EXP_TRA",
            "standard_price": 0.93,
            "can_be_expensed": True,
        })
        cls.env.user.groups_id += cls.env.ref("uom.group_uom")
        cls.env.user.action_create_employee()
        brand = cls.env["fleet.vehicle.model.brand"].create({
            "name": "Audi",
        })
        model = cls.env["fleet.vehicle.model"].create({
            "brand_id": brand.id,
            "name": "A3",
        })
        cls.vehicle_with_km_odometer = cls.env["fleet.vehicle"].create({
            "model_id": model.id,
            "driver_id": cls.env.user.partner_id.id,
            "product_id": cls.product_mileage.id
        })
        model = cls.env["fleet.vehicle.model"].create({
            "brand_id": brand.id,
            "name": "A8",
        })
        cls.vehicle_with_mi_odometer = cls.env["fleet.vehicle"].create({
            "model_id": model.id,
            "driver_id": cls.env.user.partner_id.id,
        })

    def test_01_onchange_product_can_be_used_for_fleet(self):
        self.assertEqual(self.product_expense.uom_id, self.env.ref("uom.product_uom_unit"))
        self.assertEqual(self.product_expense.uom_id_domain, [])
        self.product_expense.can_be_used_for_fleet = True
        self.product_expense.product_tmpl_id._onchange_can_be_used_for_fleet()
        uom_km = self.env.ref("uom.product_uom_km")
        uom_mile = self.env.ref("uom.product_uom_mile")
        self.assertEqual(self.product_expense.uom_id, uom_km)
        self.assertEqual(self.product_expense.uom_id_domain, [("id", "in", [uom_km.id, uom_mile.id])])
        self.product_expense.uom_id = self.env.ref("uom.product_uom_mile").id

    def test_01_onchange_odometer(self):
        self.vehicle_with_mi_odometer.product_id = self.product_expense.id
        self.odometer_in_mi = self.env["fleet.vehicle.odometer"].create(
            {"vehicle_id": self.vehicle_with_mi_odometer.id,
             "from_address": "Breda", "to_address": "Tilburg", "distance": 10.0, "is_roundtrip": True})
        self.assertEqual(self.odometer_in_mi.total_distance, 20.0)
        self.odometer_in_mi._onchange_vehicle()
        self.assertEqual(self.odometer_in_mi.product_id, self.vehicle_with_mi_odometer.product_id)
        self.odometer_in_mi.is_private_trip = True
        self.odometer_in_mi._onchange_is_private_trip()
        self.assertEqual(self.odometer_in_mi.status, "not_to_expense")
        self.odometer_in_mi.is_private_trip = False
        self.odometer_in_mi._onchange_is_private_trip()
        self.assertEqual(self.odometer_in_mi.status, "to_expense")

    def test_action_create_expense(self):
        self.odometer_in_km = self.env["fleet.vehicle.odometer"].create(
            {"vehicle_id": self.vehicle_with_km_odometer.id,
             "from_address": "Breda", "to_address": "Tilburg", "distance": 10.0})
        self.odometer_in_km._onchange_vehicle()
        self.odometer_in_mi = self.env["fleet.vehicle.odometer"].create(
            {"vehicle_id": self.vehicle_with_mi_odometer.id,
             "from_address": "Breda", "to_address": "Tilburg", "distance": 10.0, "is_roundtrip": True})
        self.odometer_in_mi._onchange_vehicle()
        (self.odometer_in_km + self.odometer_in_mi).action_create_expense()
        self.assertEqual(self.odometer_in_mi.status, "expense_created")
        self.assertEqual(self.odometer_in_mi.expense_id.quantity, 12.43)
        self.assertEqual(self.odometer_in_km.expense_id.quantity, 10.0)
