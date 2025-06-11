{
    "name": "Website Sale Share WordPress",
    "summary": "Website Sale Share WordPress",
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
            "website_sale_share_wordpress/static/src/scss/primary_variables.scss",
        ],
    },
}
