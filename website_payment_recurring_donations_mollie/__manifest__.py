# Copyright 2023 Onestein- Anjeel Haria
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Recurring donations using Mollie Subscriptions",
    "version": "18.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "category": "Website",
    "license": "LGPL-3",
    "summary": "Recurring donations using Mollie Subscriptions",
    "description": """Recurring donations using Mollie Subscriptions""",
    "depends": [
        "website_payment_recurring_donations",
        "payment_mollie_official",
        "partner_mollie",
    ],
    "data": [],
    "external_dependencies": {"python": ["mollie-api-python"]},
}
