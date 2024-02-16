# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Hr Expense Fleet",
    "version": "16.0.1.0.0",
    "category": "Human Resources/Expenses",
    "license": "LGPL-3",
    "summary": "Allows to create expenses for fleet",
    "depends": [
        "hr_expense",
        "hr_fleet",
        "product_analytic"
    ],
    "data": [
        "data/hr_expense_data.xml",
        "views/fleet_vehicle_odometer_view.xml",
        "views/fleet_vehicle_view.xml",
        "views/hr_expense_view.xml",
        "views/product_view.xml",
    ],
}
