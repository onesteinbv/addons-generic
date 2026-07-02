{
    "name": "Website Sale Share Friendica",
    "summary": "Website Sale Share Friendica",
    "category": "Website",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://onestein.nl",
    "depends": [
        "website_sale_share_base",
        "website_two_steps_share_technical",
    ],
    "data": ["templates/website_sale.xml"],
    "assets": {
        "web._assets_primary_variables": [
            "website_sale_share_friendica/static/src/scss/primary_variables.scss",
        ],
    },
}
