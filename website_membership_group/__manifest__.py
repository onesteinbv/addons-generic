# Copyright 2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Website Membership Group",
    "category": "Membership",
    "version": "16.0.1.1.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "membership_group",
        "website",
    ],
    "data": [
        "views/membership_group_view.xml",
        "views/res_partner_view.xml",
        "templates/website.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "/website_membership_group/static/src/css/website_membership.css",
        ],
    },
}
