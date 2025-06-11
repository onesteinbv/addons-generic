{
    "name": "Website Sale Share Mastodon",
    "summary": "Website Sale Share Mastodon",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "website_sale_share_base",
        "website_two_steps_share_technical",
    ],
    "data": ["templates/website_sale.xml"],
    "assets": {
        "web._assets_primary_variables": [
            "website_sale_share_mastodon/static/src/scss/primary_variables.scss",
        ],
    },
}
