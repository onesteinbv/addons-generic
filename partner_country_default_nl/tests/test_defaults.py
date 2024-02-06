# Copyright 2023 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, TransactionCase

from ..hooks import post_init_hook


class PartnerCountryDefault(TransactionCase):
    def test_01_installed_langs(self):
        """Language pack nl_NL installed by default"""
        installed_langs = dict(self.env["res.lang"].get_installed())
        self.assertIn("nl_NL", installed_langs)

        # Uninstall language pack nl_NL
        lang_nl = self.env["res.lang"].search([("code", "=", "nl_NL")])
        lang_nl.active = False
        installed_langs = dict(self.env["res.lang"].get_installed())
        self.assertNotIn("nl_NL", installed_langs)

        # Force call post_init_hook
        post_init_hook(self.cr, self.registry)
        installed_langs = dict(self.env["res.lang"].get_installed())
        self.assertIn("nl_NL", installed_langs)

    def test_02_partner_defaults(self):
        """Country set to the Netherlands and language pack is nl_NL by default"""
        partner = Form(self.env["res.partner"])
        country_nl = self.env.ref("base.nl")
        self.assertEqual(partner.country_id, country_nl)
        self.assertEqual(partner.lang, "nl_NL")
