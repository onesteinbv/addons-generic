{
    "name": "Website Sale- Share (Base)",
    "summary": "Website Sale Share (Base)",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "website_sale",
    ],
    "data": ["templates/website_sale.xml"],
    "assets": {
        "web.assets_frontend": ["website_sale_share_base/static/src/scss/website.scss"],
        "web.report_assets_common": [
            "website_sale_share_base/static/src/scss/website.scss"
        ],
    },
}
