{
    "name": "Sale - Recurring Payment",
    "version": "16.0.0.1",
    "category": "eCommerce",
    "license": "LGPL-3",
    "summary": "Sale - Recurring Payment",
    "website": "https://www.onestein.nl",
    "depends": ["subscription_oca"],
    "data": [
        "security/ir.model.access.csv",
        "data/update_payment_provider_subscription_cron.xml",
        "data/terminate_payment_provider_subscription_cron.xml",
        "views/sale_subscription_view.xml",
        "views/payment_provider_view.xml",
    ],
}
