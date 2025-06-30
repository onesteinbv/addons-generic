{
    "name": "Sale - Recurring Payment Mollie",
    "version": "18.0.1.0.0",
    "category": "eCommerce",
    "license": "LGPL-3",
    "summary": "Sale - Recurring Payment Mollie",
    "website": "https://www.onestein.nl",
    "depends": ["payment_mollie_official", "sale_recurring_payment", "partner_mollie"],
    "data": [
        "data/payment_provider.xml",
    ],
    "external_dependencies": {"python": ["mollie-api-python"]},
}
