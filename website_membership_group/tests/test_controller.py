# Copyright 2026 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestMembershipGroupController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.MembershipGroup = cls.env["membership.group"]
        cls.WebsitePage = cls.env["website.page"]
        cls.website = cls.env["website"].get_current_website()
        cls.base_view = cls.env.ref("website_membership_group.membership_group_page")

        cls.published_group = cls.MembershipGroup.create(
            {"name": "Published Controller Group", "is_published": True}
        )
        cls.unpublished_group = cls.MembershipGroup.create(
            {"name": "Unpublished Controller Group", "is_published": False}
        )
        cls.admin_user = cls.env.ref("base.user_admin")
        cls.admin_user.write(
            {"groups_id": [(4, cls.env.ref("website.group_website_designer").id)]}
        )

    def test_01_public_user_can_view_published_group(self):
        """A published group's page should be publicly reachable (HTTP 200)."""
        response = self.url_open(self.published_group.website_url)
        self.assertEqual(response.status_code, 200)

    def test_02_public_user_gets_404_for_unpublished_group(self):
        """An unpublished group should return a 404 to a public (anonymous)
        visitor."""
        url = "/members/group/%s" % self.env["ir.http"]._slug(self.unpublished_group)
        response = self.url_open(url)
        self.assertEqual(response.status_code, 404)

    def test_03_designer_triggers_page_auto_creation_for_unpublished_group(self):
        """A website designer visiting an unpublished group that has no
        page_id yet should trigger `_create_unique_website_page` and be
        redirected to the newly created page."""
        self.assertFalse(self.unpublished_group.page_id)
        self.authenticate("admin", "admin")

        url = "/members/group/%s" % self.env["ir.http"]._slug(self.unpublished_group)
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        self.unpublished_group.invalidate_recordset()
        self.assertTrue(self.unpublished_group.page_id)

    def test_04_designer_can_view_unpublished_group_with_existing_page(self):
        """A website designer visiting an unpublished group that already has
        a page_id should have that page rendered directly (no redirect)."""
        group = self.MembershipGroup.create(
            {
                "name": "Designer Existing Page Group",
                "is_published": False,
            }
        )
        slug = self.env["ir.http"]._slug(group)
        page = self.WebsitePage.create(
            {
                "view_id": self.base_view.copy(
                    {
                        "name": "Designer Existing Page View",
                        "key": "website_membership_group.test_view_designer",
                        "type": "qweb",
                        "website_id": self.website.id,
                    }
                ).id,
                "url": f"/members/group/{slug}",
                "is_published": False,
                "website_id": self.website.id,
            }
        )
        group.write({"page_id": page.id})
        self.authenticate("admin", "admin")
        response = self.url_open(page.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(group.name, response.text)

    def test_05_published_group_renders_group_name(self):
        """The rendered page for a published group should contain its name."""
        response = self.url_open(self.published_group.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.published_group.name, response.text)
