# Copyright 2020-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sales Team Disabled",
    "summary": "Hide Sales Team feature",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": [
        "sales_team",
    ],
    "data": [
        "security/sales_team_security.xml",
        "views/crm_team.xml",
    ],
    "installable": True,
}
