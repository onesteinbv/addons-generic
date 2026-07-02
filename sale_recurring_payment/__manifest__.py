{
    "name": "Sale - Recurring Payment",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "category": "eCommerce",
    "license": "LGPL-3",
    "summary": "Sale - Recurring Payment",
    "website": "https://onestein.nl",
    "depends": ["subscription_oca", "account_payment"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/sale_subscription_view.xml",
        "views/payment_provider_view.xml",
        "views/payment_provider_mandate_view.xml",
    ],
}
