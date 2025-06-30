{
    "name": "Website Partner Privacy",
    "summary": "Adds an option to define website privacy options for partners",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "category": "Website",
    "depends": ["website_partner"],
    "data": [
        "templates/portal_template.xml",
        "views/res_partner.xml",
        "views/website_partner_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_partner_privacy/static/src/js/portal.js",
        ],
    },
    "auto_install": False,
    "installable": True,
}
