# Copyright 2022-2023 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Base Municipality",
    "summary": "Manage municipality informations on contacts",
    "version": "16.0.1.0.0",
    "category": "Partner Management",
    "website": "https://www.onestein.nl",
    "author": "Onestein",
    "license": "AGPL-3",
    "depends": [
        "contacts",
    ],
    "data": [
        "data/res.country.municipality.csv",
        "security/ir.model.access.csv",
        "views/res_country_municipality_view.xml",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "menuitems.xml",
    ],
}
