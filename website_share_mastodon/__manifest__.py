{
    "name": "Website Share Mastodon",
    "summary": "Website Share Mastodon",
    "category": "Website",
    "version": "16.0.1.0.1",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "website",
        "website_share_base",
        "website_two_steps_share_technical",
    ],
    "data": ["views/snippets/s_share.xml"],
    "assets": {
        "web._assets_primary_variables": [
            "website_share_mastodon/static/src/scss/primary_variables.scss",
        ],
    },
}
