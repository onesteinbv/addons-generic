# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Netherlands - RGS Accounting (3.5.2)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations/Account Charts',
    'author': 'Onestein',
    'website': 'https://www.onestein.nl',
    'depends': [
        'account',
        'l10n_nl',
        'account_journal_subtype',
    ],
    'data': [
        'data/account_account_tag.xml',
        'views/res_config_settings_views.xml',
        'views/account_account_views.xml',
        'views/account_group_views.xml',
    ],
    'demo': [
        'demo/demo_company.xml',
    ],
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
