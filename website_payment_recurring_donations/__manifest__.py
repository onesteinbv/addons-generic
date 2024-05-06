# Copyright 2023 Onestein- Anjeel Haria
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Recurring donations",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "website": "https://www.onestein.nl",
    "category": "Website",
    "license": "LGPL-3",
    "summary": "Recurring donations",
    "description": """Recurring donations""",
    "depends": ["website_payment"],
    "data": [
        "data/donation_data.xml",
        "views/snippets/s_donation.xml",
        "views/donation_templates.xml",
        "views/payment_transaction_view.xml",
        "views/res_partner_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_payment_recurring_donations/static/src/js/website_payment_form.esm.js",
        ],
    },
}
