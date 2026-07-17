# Copyright 2026 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestMembershipGroup(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.MembershipGroup = cls.env["membership.group"]
        cls.WebsitePage = cls.env["website.page"]
        cls.website = cls.env["website"].get_current_website()
        cls.base_view = cls.env.ref("website_membership_group.membership_group_page")

    @classmethod
    def _make_page(cls, url, is_published=False, key_suffix="x"):
        """Helper: create a standalone website.page cloned from the base template,
        mimicking what `_create_unique_website_page` does, so we can pre-seed
        pages for the various sync scenarios.
        """
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

    def test_01_default_field_values(self):
        """New groups should get the expected default snippet class values."""
        group = self.MembershipGroup.create({"name": "Defaults Group"})
        self.assertEqual(
            group.website_snippet_wrap_classes, "mg_wrap mg_show_image mg_show_team"
        )
        self.assertEqual(
            group.website_snippet_members_classes, "mg_layout_grid mg_show_team_desc"
        )
        self.assertEqual(group.website_team_col_classes, "col-lg-12")
        self.assertEqual(group.website_header_image_col_classes, "col-lg-4")
        self.assertEqual(group.website_header_desc_col_classes, "col-lg-8")
        self.assertFalse(group.website_hide_member_type_ids)

    def test_02_compute_website_url_without_page(self):
        """Without a linked page, website_url should fall back to the
        `/members/group/<slug>` pattern."""
        group = self.MembershipGroup.create({"name": "No Page Group"})
        slug = self.env["ir.http"]._slug(group)
        self.assertEqual(group.website_url, "/members/group/%s" % slug)

    def test_03_compute_website_url_with_page(self):
        """When a page is linked, website_url should mirror the page's own url."""
        group = self.MembershipGroup.create({"name": "With Page Group"})
        page = self._make_page("/members/group/with-page-group", key_suffix="wpg")
        group.page_id = page.id
        self.assertEqual(group.website_url, page.url)

        # changing the page url should recompute the group's website_url too
        page.url = "/members/group/renamed-url"
        self.assertEqual(group.website_url, "/members/group/renamed-url")

    def test_04_create_syncs_page_publish_state(self):
        """Creating a group with a page_id whose publish state differs from the
        group's should push the group's is_published value onto the page."""
        page = self._make_page(
            "/members/group/create-sync", is_published=False, key_suffix="create1"
        )
        group = self.MembershipGroup.create(
            {"name": "Create Sync Group", "page_id": page.id, "is_published": True}
        )
        self.assertTrue(page.is_published)
        self.assertEqual(group.is_published, page.is_published)

    def test_05_create_no_page_does_not_raise(self):
        """Creating a group without a page_id should simply skip the sync logic."""
        group = self.MembershipGroup.create(
            {"name": "No Page Sync Group", "is_published": True}
        )
        self.assertFalse(group.page_id)
        self.assertTrue(group.is_published)

    def test_06_write_is_published_syncs_page(self):
        """Toggling is_published on the group should propagate to its page."""
        page = self._make_page(
            "/members/group/write-sync-1", is_published=True, key_suffix="write1"
        )
        group = self.MembershipGroup.create(
            {"name": "Write Sync Group", "page_id": page.id, "is_published": True}
        )
        self.assertTrue(page.is_published)

        group.write({"is_published": False})
        self.assertFalse(page.is_published)

        group.write({"is_published": True})
        self.assertTrue(page.is_published)

    def test_07_write_page_id_syncs_publish_state(self):
        """Assigning a new page_id via write should sync the new page's
        publish state to match the group's."""
        group = self.MembershipGroup.create(
            {"name": "Reassign Page Group", "is_published": True}
        )
        new_page = self._make_page(
            "/members/group/write-sync-2", is_published=False, key_suffix="write2"
        )
        group.write({"page_id": new_page.id})
        self.assertTrue(new_page.is_published)

    def test_08_write_unrelated_field_does_not_touch_page(self):
        """Writing a field other than is_published/page_id should not trigger
        the sync logic (and, in particular, should not error out)."""
        page = self._make_page(
            "/members/group/write-sync-3", is_published=False, key_suffix="write3"
        )
        group = self.MembershipGroup.create(
            {"name": "Untouched Page Group", "page_id": page.id, "is_published": False}
        )
        self.assertFalse(page.is_published)

        group.write({"name": "Renamed Untouched Page Group"})
        self.assertFalse(page.is_published)
        self.assertEqual(group.name, "Renamed Untouched Page Group")

    def test_09_create_unique_website_page_returns_existing_linked_page(self):
        """If the group already has a page_id, the method should return it
        as-is without creating anything new."""
        page = self._make_page("/members/group/already-linked", key_suffix="linked")
        group = self.MembershipGroup.create(
            {"name": "Already Linked Group", "page_id": page.id}
        )
        page_count_before = self.WebsitePage.search_count([])

        result = group._create_unique_website_page()

        self.assertEqual(result, page)
        self.assertEqual(self.WebsitePage.search_count([]), page_count_before)

    def test_10_create_unique_website_page_reuses_matching_url(self):
        """If a website.page already exists at the expected url (but is not
        yet linked as page_id), the method should link it instead of creating
        a duplicate page."""
        group = self.MembershipGroup.create({"name": "Reuse Url Group"})
        slug = self.env["ir.http"]._slug(group)
        expected_url = f"/members/group/{slug}"

        pre_existing_page = self._make_page(expected_url, key_suffix="preexisting")
        page_count_before = self.WebsitePage.search_count([])

        result = group._create_unique_website_page()

        self.assertEqual(result, pre_existing_page)
        self.assertEqual(group.page_id, pre_existing_page)
        self.assertEqual(self.WebsitePage.search_count([]), page_count_before)

    def test_11_create_unique_website_page_creates_new_page(self):
        """When there is no page_id and no matching existing url, a brand new
        website.page (and its underlying view) should be created."""
        group = self.MembershipGroup.create(
            {"name": "Brand New Page Group", "is_published": True}
        )
        slug = self.env["ir.http"]._slug(group)
        expected_url = f"/members/group/{slug}"

        result = group._create_unique_website_page()

        self.assertEqual(group.page_id, result)
        self.assertEqual(result.url, expected_url)
        self.assertEqual(result.is_published, group.is_published)
        self.assertEqual(result.website_id, self.website)
        self.assertEqual(
            result.view_id.key,
            f"website_membership_group.membership_group_page_{group.id}",
        )

    def test_12_create_unique_website_page_ensure_one(self):
        """The method should refuse to run on a multi-record recordset."""
        group_a = self.MembershipGroup.create({"name": "Ensure One A"})
        group_b = self.MembershipGroup.create({"name": "Ensure One B"})
        groups = group_a + group_b
        with self.assertRaises(ValueError):
            groups._create_unique_website_page()
