# Copyright 2020-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sales Team Disabled - CRM",
    "summary": "Hide Sales Team in CRM App",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": [
        "crm",
        "sales_team_disabled",
    ],
    "data": [
        "views/crm_lead.xml",
        "views/crm_stage.xml",
        "views/crm_activity_report.xml",
    ],
    "auto_install": True,
    "installable": True,
}
