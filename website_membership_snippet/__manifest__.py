# Copyright 2026 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Website Membership Snippet",
    "category": "Membership",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "website_membership_group",
    ],
    "data": [
        "data/website_snippet_filter_data.xml",
        "views/snippets/dynamic_templates.xml",
        "views/snippets/snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_membership_snippet/static/src/js/membership_snippet.esm.js",
        ],
        "website.assets_wysiwyg": [
            "website_membership_snippet/static/src/js/membership_snippet_options.esm.js",
        ],
    },
}
