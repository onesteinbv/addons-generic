# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMembershipRegistrationMenu(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].create(
            {
                "name": "Membership Registration Test Website",
                "domain": "https://membership-registration-test.example.com",
            }
        )
        cls.menu_model = cls.env["website.menu"]
        cls.menu_url = "/membership-registration"

    def _create_settings(self, allow_registration):
        return self.env["res.config.settings"].create(
            {
                "website_id": self.website.id,
                "allow_membership_registration": allow_registration,
            }
        )

    def _find_registration_menus(self, website=None):
        website = website or self.website
        return self.menu_model.search(
            [
                ("url", "=", self.menu_url),
                ("website_id", "=", website.id),
            ]
        )

    def test_enable_registration_creates_menu(self):
        """Enabling registration creates the website menu with correct values."""
        settings = self._create_settings(True)

        settings.set_values()

        menu = self._find_registration_menus()
        self.assertEqual(len(menu), 1)
        self.assertEqual(menu.name, "Membership Registration")
        self.assertEqual(menu.url, self.menu_url)
        self.assertEqual(menu.parent_id, self.website.menu_id)
        self.assertEqual(menu.sequence, 200)
        self.assertEqual(menu.website_id, self.website)

    def test_enable_registration_does_not_duplicate_menu(self):
        """Saving enabled settings repeatedly must not duplicate the menu."""
        settings = self._create_settings(True)

        settings.set_values()
        settings.set_values()

        self.assertEqual(len(self._find_registration_menus()), 1)

    def test_disable_registration_removes_existing_menu(self):
        """Disabling registration removes its website menu."""
        menu = self.menu_model.create(
            {
                "name": "Membership Registration",
                "url": self.menu_url,
                "parent_id": self.website.menu_id.id,
                "sequence": 200,
                "website_id": self.website.id,
            }
        )
        settings = self._create_settings(False)

        settings.set_values()

        self.assertFalse(menu.exists())
        self.assertFalse(self._find_registration_menus())

    def test_disable_registration_without_menu(self):
        """Disabling registration works when the menu does not exist."""
        settings = self._create_settings(False)

        settings.set_values()

        self.assertFalse(self._find_registration_menus())

    def test_registration_menu_is_website_specific(self):
        """Disabling registration on one website preserves another website's menu."""
        other_website = self.env["website"].create(
            {
                "name": "Other Membership Test Website",
                "domain": "https://other-membership-test.example.com",
            }
        )
        other_menu = self.menu_model.create(
            {
                "name": "Membership Registration",
                "url": self.menu_url,
                "parent_id": other_website.menu_id.id,
                "sequence": 200,
                "website_id": other_website.id,
            }
        )
        settings = self._create_settings(False)

        settings.set_values()

        self.assertFalse(self._find_registration_menus())
        self.assertTrue(other_menu.exists())
        self.assertEqual(other_menu.website_id, other_website)

    def test_registration_link_is_present_in_settings_view(self):
        """The settings view contains the membership registration link."""
        view = self.env.ref(
            "website_membership_registration.res_config_settings_view_form"
        )

        self.assertIn("/membership-registration", view.arch)
        self.assertIn("not allow_membership_registration", view.arch)
