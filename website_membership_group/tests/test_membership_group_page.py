from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestMembershipGroupPage(HttpCase):
    """Tests for the membership group unique page creation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env["membership.group"].create(
            {
                "name": "Page Test Group",
            }
        )

    def test_page_created_on_publish(self):
        """Publishing a group auto-creates a unique website.page."""
        self.assertFalse(self.group.page_id)
        self.group.is_published = True
        self.assertTrue(self.group.page_id)
        self.assertTrue(self.group.page_id.is_published)

    def test_page_not_accessible_when_unpublished(self):
        """Unpublished groups return 404 for public users."""
        self.group.is_published = True
        self.group.is_published = False
        response = self.url_open(f"/members/group/{self.group.id}-page-test-group")
        self.assertEqual(response.status_code, 404)

    def test_page_is_unique_per_group(self):
        """Each group gets its own page and view."""
        self.group.write({"is_published": True})
        group2 = self.env["membership.group"].create(
            {
                "name": "Another Group",
            }
        )
        group2.write({"is_published": True})
        self.assertTrue(self.group.page_id)
        self.assertTrue(group2.page_id)
        self.assertNotEqual(self.group.page_id, group2.page_id)
        self.assertNotEqual(self.group.page_id.view_id, group2.page_id.view_id)

    def test_page_unpublish_sync(self):
        """Unpublishing a group also unpublishes its page."""
        self.group.write({"is_published": True})
        self.assertTrue(self.group.page_id.is_published)
        self.group.write({"is_published": False})
        self.assertFalse(self.group.page_id.is_published)
