# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Website Membership Registration Partner Privacy Nickname",
    "category": "Website",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "website_membership_registration_partner_privacy",
        "website_partner_privacy_nickname",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_membership_registration_partner_privacy_nickname/static/src/js/website_membership_registration.js",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": True,
}
