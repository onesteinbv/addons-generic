{
    "name": "ArgoCD Frontend",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "category": "Sales",
    "version": "16.0.1.0.0",
    "depends": [
        "website",
        "payment",
        "argocd_sale",
        "portal",
        "auth_signup",
        "base_librecaptcha",
        "product_category_sequence",
    ],
    "data": [
        "data/mail_template_data.xml",
        "security/ir_model_access.xml",
        "security/ir_rule.xml",
        "templates/website.xml",
        "templates/portal.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "argocd_website/static/src/js/portal.js",
            "argocd_website/static/src/scss/portal.scss",
        ]
    },
    "external_dependencies": {"python": ["yaml", "requests", "dnspython==2.6.1"]},
}
