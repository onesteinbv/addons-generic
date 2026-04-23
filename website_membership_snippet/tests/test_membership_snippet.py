from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestMembershipSnippet(HttpCase):
    """Tests for the website membership snippet endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env["membership.group"].create({
            "name": "Test Group",
            "is_published": True,
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Member",
            "website_published": True,
        })
        cls.env["membership.group.member"].create({
            "group_id": cls.group.id,
            "partner_id": cls.partner.id,
            "type": "committee",
            "state": "current",
        })

    def test_snippet_groups_endpoint(self):
        """The /membership/snippet/groups endpoint returns published groups."""
        result = self.url_open(
            "/membership/snippet/groups",
            data='{"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertIn("result", data)
        group_names = [g["name"] for g in data["result"]]
        self.assertIn("Test Group", group_names)

    def test_snippet_members_endpoint(self):
        """The /membership/snippet/members endpoint returns group members."""
        result = self.url_open(
            "/membership/snippet/members",
            data='{"jsonrpc": "2.0", "method": "call", "params": {"group_id": %s}, "id": 1}' % self.group.id,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertIn("result", data)
        member_names = [m["name"] for m in data["result"]]
        self.assertIn("Test Member", member_names)

    def test_snippet_members_unpublished_group(self):
        """Unpublished groups are not returned by the groups endpoint."""
        self.group.is_published = False
        result = self.url_open(
            "/membership/snippet/groups",
            data='{"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}',
            headers={"Content-Type": "application/json"},
        )
        data = result.json()
        group_names = [g["name"] for g in data["result"]]
        self.assertNotIn("Test Group", group_names)

    def test_snippet_members_unpublished_partner(self):
        """Unpublished partners are not included in member results."""
        self.partner.website_published = False
        result = self.url_open(
            "/membership/snippet/members",
            data='{"jsonrpc": "2.0", "method": "call", "params": {"group_id": %s}, "id": 1}' % self.group.id,
            headers={"Content-Type": "application/json"},
        )
        data = result.json()
        member_names = [m["name"] for m in data["result"]]
        self.assertNotIn("Test Member", member_names)
