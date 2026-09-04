# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Spreadsheet dashboard for membership",
    "version": "18.0.1.0.0",
    "category": "Hidden",
    "author": "CIT-Services, Onestein",
    "website": "https://onestein.nl",
    "summary": "Spreadsheet",
    "depends": ["spreadsheet_dashboard", "membership"],
    "data": [
        "data/dashboards.xml",
    ],
    "auto_install": ["membership"],
    "license": "LGPL-3",
}
