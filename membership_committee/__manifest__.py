# Copyright 2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Membership Committee",
    "category": "Membership",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "contacts",
        "membership",
        "membership_section",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/membership_committee_view.xml",
        "views/res_partner_view.xml",
        "views/membership_section_view.xml",
        "menuitems.xml",
    ],
    "demo": [
        "data/membership_committee_demo.xml",
        "data/res_partner_demo.xml",
    ],
}
