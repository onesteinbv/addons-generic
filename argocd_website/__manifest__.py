{
    "name": "ArgoCD Frontend",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "category": "Sales",
    "version": "18.0.1.0.0",
    "depends": [
        "website",
        "payment",
        "account_payment",
        "argocd_sale",
        "portal",
        "auth_signup",
        "base_librecaptcha",
        "product_category_sequence",
        "subscription_portal",
    ],
    "data": [
        "data/ir_config_parameter_data.xml",
        "data/ir_cron.xml",
        "security/ir_model_access.xml",
        "security/ir_rule.xml",
        "templates/website.xml",
        "templates/portal.xml",
        "templates/customer_portal.xml",
    ],
    "demo": ["demo/ir_config_parameter_demo.xml"],
    "assets": {
        "web.assets_frontend": [
            "argocd_website/static/src/js/portal.esm.js",
            "argocd_website/static/src/js/website.esm.js",
            "argocd_website/static/src/scss/portal.scss",
            "argocd_website/static/src/scss/website.scss",
            "argocd_website/static/src/xml/website.xml",
        ]
    },
    "external_dependencies": {"python": ["pyyaml", "requests", "dnspython==2.6.1"]},
}
