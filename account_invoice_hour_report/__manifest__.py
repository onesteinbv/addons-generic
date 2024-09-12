# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Invoice hour report addition",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "category": "Accounting & Finance",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "depends": [
        "sale_timesheet_approval",
        "sale_timesheet_custom_fields",
    ],
    "data": [
        "templates/hour_report_template.xml",
        "views/hours_report.xml",
        "views/res_partner.xml",
    ],
    "installable": True,
}
