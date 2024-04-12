# Copyright 2023 Onestein- Anjeel Haria
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Recurring donations using Mollie Subscriptions',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'license': 'LGPL-3',
    'summary': 'Recurring donations using Mollie Subscriptions',
    'description': """Recurring donations using Mollie Subscriptions""",
    'depends': ["website_payment_recurring_donations", "payment_mollie_official"],
    'data': [
        "views/res_partner_view.xml",
    ],
    'external_dependencies': {
            'python': ['mollie-api-python']
    },
}
