{
    "name": "Website - Share (Base)",
    "summary": "Website Share (Base)",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://onestein.nl",
    "depends": [
        "web",
        "website",
    ],
    "data": [
        "views/snippets/s_share.xml",
    ],
    "assets": {
        "web.assets_frontend": ["website_share_base/static/src/scss/website.scss"],
        "web.report_assets_common": ["website_share_base/static/src/scss/website.scss"],
    },
}
