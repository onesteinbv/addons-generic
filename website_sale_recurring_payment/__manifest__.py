{
    "name": "Website Sale - Recurring Payment",
    "version": "16.0.0.1",
    "category": "eCommerce",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "LGPL-3",
    "summary": "Website Sale - Recurring Payment",
    "depends": ["contract", "payment", "product_contract", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/update_contract_payment_subscription_cron.xml",
        "data/terminate_provider_subscription_cron.xml",
        "views/contract_view.xml",
        "views/payment_provider.xml",
    ],
}
