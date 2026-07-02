# Copyright 2022 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Mass Mailing Membership Group",
    "category": "Membership",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://onestein.nl",
    "depends": [
        "mass_mailing",
        "mass_mailing_partner",
        "membership",
        "membership_group",
    ],
    "data": [
        "views/membership_group_view.xml",
        "views/membership_group_member_view.xml",
    ],
    "demo": [
        "data/mailing_list_demo.xml",
        "data/membership_group_demo.xml",
        "data/mailing_contact_demo.xml",
        "data/res_partner_demo.xml",
    ],
    "auto_install": True,
}
