# Copyright 2023 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Membership Mollie Subscription",
    "category": "Membership",
    "version": "16.0.1.0.0",
    "author": "Onestein",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "membership",
        "mollie_subscription_ept",
    ],
    "data": [
        "views/membership_product_view.xml",
    ],
    "auto_install": True,
}
