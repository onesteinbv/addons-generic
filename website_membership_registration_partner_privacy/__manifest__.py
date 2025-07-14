# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Website Membership Registration Partner Privacy",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": ["website_membership_registration", "website_partner_privacy"],
    "data": [
        "templates/website.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_membership_registration_partner_privacy/static/src/js/website_membership_registration_partner_privacy.esm.js",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": True,
}
