{
    "name": "Website Sale - Recurring Payment Mollie",
    "version": "16.0.0.1",
    "category": "eCommerce",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "license": "LGPL-3",
    "summary": "Website Sale - Recurring Payment Mollie",
    "depends": [
        "contract",
        "contract_mandate",
        "payment_mollie_official",
        "product_contract",
        "sale_management",
        "website_sale_recurring_payment",
    ],
    "data": [
        "data/payment_provider.xml",
        "views/partner_view.xml",
    ],
    "external_dependencies": {"python": ["mollie-api-python"]},
}
