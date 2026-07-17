# Copyright 2026 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestWebsitePage(BaseCommon):
    """Tests for the `website.page` extension that syncs `is_published`
    back onto any `membership.group` linked through `page_id`.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.MembershipGroup = cls.env["membership.group"]
        cls.WebsitePage = cls.env["website.page"]
        cls.website = cls.env["website"].get_current_website()
        cls.base_view = cls.env.ref("website_membership_group.membership_group_page")

    @classmethod
    def _make_page(cls, url, is_published=False, key_suffix="x"):
        new_view = cls.base_view.copy(
            {
                "name": f"Test View {key_suffix}",
                "key": f"website_membership_group.test_view_{key_suffix}",
                "type": "qweb",
                "website_id": cls.website.id,
            }
        )
        return cls.WebsitePage.create(
            {
                "view_id": new_view.id,
                "url": url,
                "is_published": is_published,
                "website_id": cls.website.id,
            }
        )

    def test_01_page_write_publishes_linked_group(self):
        """Publishing a page should publish its linked membership group."""
        page = self._make_page(
            "/members/group/page-write-1", is_published=False, key_suffix="pw1"
        )
        group = self.MembershipGroup.create(
            {"name": "Page Write Group 1", "page_id": page.id, "is_published": False}
        )

        page.write({"is_published": True})
        self.assertTrue(group.is_published)

    def test_02_page_write_unpublishes_linked_group(self):
        """Unpublishing a page should unpublish its linked membership group."""
        page = self._make_page(
            "/members/group/page-write-2", is_published=True, key_suffix="pw2"
        )
        group = self.MembershipGroup.create(
            {"name": "Page Write Group 2", "page_id": page.id, "is_published": True}
        )

        page.write({"is_published": False})
        self.assertFalse(group.is_published)

    def test_03_page_write_no_linked_group(self):
        """Toggling publish state of a page with no linked group should not
        error out and should simply be a no-op regarding groups."""
        page = self._make_page(
            "/members/group/page-write-3", is_published=False, key_suffix="pw3"
        )
        page.write({"is_published": True})
        self.assertTrue(page.is_published)

    def test_04_page_write_same_publish_state_is_noop(self):
        """If the group already matches the page's publish state, writing the
        same state again should not raise and should leave things consistent."""
        page = self._make_page(
            "/members/group/page-write-4", is_published=True, key_suffix="pw4"
        )
        group = self.MembershipGroup.create(
            {"name": "Page Write Group 4", "page_id": page.id, "is_published": True}
        )

        page.write({"is_published": True})
        self.assertTrue(group.is_published)

    def test_05_page_write_unrelated_field_does_not_affect_group(self):
        """Writing a field other than is_published should not touch the
        linked group's publish state."""
        page = self._make_page(
            "/members/group/page-write-5", is_published=False, key_suffix="pw5"
        )
        group = self.MembershipGroup.create(
            {"name": "Page Write Group 5", "page_id": page.id, "is_published": False}
        )

        page.write({"url": "/members/group/page-write-5-renamed"})
        self.assertFalse(group.is_published)
        self.assertEqual(page.url, "/members/group/page-write-5-renamed")

    def test_06_page_write_only_updates_mismatched_groups(self):
        """Only groups whose is_published differs from the page should be
        written; a group already matching should be left alone (and not
        error even though it's excluded from the search domain)."""
        page = self._make_page(
            "/members/group/page-write-6", is_published=False, key_suffix="pw6"
        )
        matching_group = self.MembershipGroup.create(
            {
                "name": "Already Matching Group",
                "page_id": page.id,
                "is_published": False,
            }
        )
        page.write({"is_published": False})
        self.assertFalse(matching_group.is_published)
