# Copyright 2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Website Membership Group",
    "category": "Membership",
    "version": "18.0.1.0.3",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://onestein.nl",
    "depends": [
        "membership_group",
        "website_membership",
    ],
    "data": [
        "views/membership_group_view.xml",
        "templates/website.xml",
        "views/snippets/snippet_options.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_membership_group/static/src/scss/membership_group.scss",
            "website_membership_group/static/src/js/membership_group_frontend.esm.js",
        ],
        "website.assets_wysiwyg": [
            "website_membership_group/static/src/js/membership_group_options.esm.js",
        ],
    },
}
