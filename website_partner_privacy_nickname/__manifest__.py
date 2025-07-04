{
    "name": "Website Partner Privacy Nickname",
    "summary": "Adds an option to define nickname as one of the options for website privacy setting for partners",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "category": "Website",
    "depends": ["website_partner_privacy", "partner_nickname"],
    "data": ["views/res_partner.xml"],
    "assets": {
        "web.assets_frontend": [
            "website_partner_privacy_nickname/static/src/js/portal.js",
        ],
    },
    "auto_install": True,
    "installable": True,
}
