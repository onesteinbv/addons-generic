# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Timesheet Approval",
    "version": "16.0.1.0.0",
    "summary": "Timesheet Approval management",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "category": "Human Resources",
    "depends": [
        "sale_timesheet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_analytic_line_data.xml",
        "views/hr_timesheet_views.xml",
        "wizard/hr_timesheet_invoice_create_view.xml",
    ],
    "post_init_hook": "set_is_approved",
    "installable": True,
}
