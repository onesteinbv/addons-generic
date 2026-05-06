# Copyright 2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Website Membership Group",
    "category": "Membership",
    "version": "18.0.1.0.3",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "membership_group",
        "website_membership",
    ],
    "data": [
        "data/website_snippet_filter_data.xml",
        "views/membership_group_view.xml",
        "templates/website.xml",
        "views/snippets/snippet_options.xml",
        "views/snippets/dynamic_templates.xml",
        "views/snippets/members_snippet.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_membership_group/static/src/scss/membership_group.scss",
            "website_membership_group/static/src/js/membership_group_frontend.esm.js",
            "website_membership_group/static/src/js/membership_snippet.esm.js",
        ],
        "website.assets_wysiwyg": [
            "website_membership_group/static/src/js/membership_group_options.esm.js",
            "website_membership_group/static/src/js/membership_snippet_options.esm.js",
        ],
    },
}
