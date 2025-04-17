# Copyright 2023 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Membership Group",
    "category": "Membership",
    "version": "16.0.1.0.1",
    "author": "Onestein, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://www.onestein.nl",
    "depends": [
        "contacts",
        "membership",
    ],
    "data": [
        "data/ir_actions_server_data.xml",
        "data/ir_cron_data.xml",
        "security/ir.model.access.csv",
        "views/membership_group_member_view.xml",
        "views/membership_group_view.xml",
        "views/res_partner_view.xml",
        "wizard/membership_history_wizard_view.xml",
        "menuitems.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "membership_group/static/src/views/**/*",
        ],
    },
    "demo": [
        "data/membership_group_demo.xml",
        "data/res_partner_demo.xml",
    ],
}
