# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Website Membership Registration Partner Nickname",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://onestein.nl",
    "depends": ["website_membership_registration", "partner_nickname"],
    "data": [
        "templates/website.xml",
    ],
    "demo": [
        "data/res_partner_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": True,
}
