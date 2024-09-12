# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Timesheet Sheet Approval",
    "summary": "Timesheet Sheet Approval management",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": [
        "sale_timesheet_approval",
        "hr_timesheet_sheet",
    ],
    "data": [
        "views/hr_timesheet_views.xml",
    ],
    "auto_install": True,
    "installable": True,
}
