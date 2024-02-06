# Copyright 2016-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """
    Post-install script. Install nl_NL language pack if not already installed.
    """
    logging.getLogger("odoo.addons.partner_country_default_nl").info(
        "Check/Install nl_NL language pack"
    )

    env = api.Environment(cr, SUPERUSER_ID, {})
    installed_langs = dict(env["res.lang"].get_installed())
    if "nl_NL" not in installed_langs:
        env["res.lang"]._activate_lang("nl_NL")
