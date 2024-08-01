{
    "name": "ArgoCD Sales Management",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "AGPL-3",
    "category": "Sales",
    "version": "16.0.1.0.0",
    "depends": [
        "sale",
        "subscription_oca",
        "argocd_deployer",
        "sale_recurring_payment",
    ],
    "demo": [
        "demo/sale_subscription_template_demo.xml",
        "demo/product_template_demo.xml",
    ],
    "data": [
        "data/mail_template_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/product_template.xml",
        "views/application_view.xml",
        "views/res_config_settings_view.xml",
        "views/sale_subscription_view.xml",
        "views/product_attribute_view.xml",
    ],
}
