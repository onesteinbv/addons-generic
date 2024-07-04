{
    "name": "Sale - Recurring Payment",
    "version": "16.0.0.1",
    "category": "eCommerce",
    "license": "LGPL-3",
    "summary": "Sale - Recurring Payment",
    "website": "https://www.onestein.nl",
    "depends": ["subscription_oca", "account_payment"],
    "data": [
        "security/ir.model.access.csv",
        "data/update_payment_provider_payments_cron.xml",
        "views/sale_subscription_view.xml",
        "views/payment_provider_view.xml",
    ],
}
