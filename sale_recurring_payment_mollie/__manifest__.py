{
    "name": "Sale - Recurring Payment Mollie",
    "version": "16.0.0.1",
    "category": "eCommerce",
    "license": "LGPL-3",
    "summary": "Sale - Recurring Payment Mollie",
    "website": "https://www.onestein.nl",
    "depends": ["payment_mollie_official", "sale_recurring_payment"],
    "data": [
        "data/payment_provider.xml",
        "views/partner_view.xml",
    ],
    "external_dependencies": {"python": ["mollie-api-python"]},
}
