# Copyright 2020-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sales Team Disabled - Sale",
    "summary": "Hide Sales Team in Sales App",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": [
        "sale_management",
        "sales_team_disabled",
    ],
    "data": [
        "views/account_move.xml",
        "views/sale_order.xml",
        "views/sale_report.xml",
    ],
    "auto_install": True,
    "installable": True,
}
