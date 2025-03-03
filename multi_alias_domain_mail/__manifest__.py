# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Multi Alias Domain",
    "summary": "Allows to add multiple domains for aliases",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "Onestein BV",
    "website": "https://www.onestein.eu",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/mail_alias_domain_views.xml",
        "views/mail_alias_views.xml",
        "views/res_company_views.xml",
        "views/res_config_settings_view.xml",
        "wizard/mail_compose_message_view.xml",
    ],
    "installable": True,
    "post_init_hook": "_mail_post_init",
}
