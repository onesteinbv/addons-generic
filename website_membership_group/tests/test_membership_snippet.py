from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestMembershipSnippet(HttpCase):
    """Tests for the membership members dynamic snippet."""

    def test_snippet_filter_exists(self):
        """The dynamic snippet filter record exists."""
        filter_record = self.env.ref(
            "website_membership_group.dynamic_filter_membership_members",
            raise_if_not_found=False,
        )
        self.assertTrue(filter_record)
        self.assertEqual(filter_record.model_name, "res.partner")
        self.assertEqual(filter_record.limit, 16)

    def test_snippet_groups_endpoint(self):
        """The /membership/snippet/groups endpoint returns published groups."""
        self.env["membership.group"].create(
            {
                "name": "Test Group",
                "is_published": True,
            }
        )
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

    def test_dynamic_filter_renders_members(self):
        """The dynamic filter renders members for a published group."""
        group = self.env["membership.group"].create(
            {
                "name": "Dynamic Test Group",
                "is_published": True,
            }
        )
        partner = self.env["res.partner"].create(
            {
                "name": "Dynamic Test Member",
                "website_published": True,
            }
        )
        self.env["membership.group.member"].create(
            {
                "group_id": group.id,
                "partner_id": partner.id,
                "type": "committee",
                "state": "current",
            }
        )

        filter_record = self.env.ref(
            "website_membership_group.dynamic_filter_membership_members"
        )
        fragments = filter_record._render(
            "website_membership_group.dynamic_filter_template_res_partner_grid",
            limit=16,
            search_domain=[("membership_group_member_ids.group_id", "=", group.id)],
        )
        self.assertTrue(fragments)
        self.assertIn("Dynamic Test Member", fragments[0])

    def test_dynamic_filter_hides_unpublished_members(self):
        """Unpublished partners are not rendered."""
        group = self.env["membership.group"].create(
            {
                "name": "Hidden Member Group",
                "is_published": True,
            }
        )
        partner = self.env["res.partner"].create(
            {
                "name": "Hidden Member",
                "website_published": False,
            }
        )
        self.env["membership.group.member"].create(
            {
                "group_id": group.id,
                "partner_id": partner.id,
                "type": "committee",
                "state": "current",
            }
        )

        filter_record = self.env.ref(
            "website_membership_group.dynamic_filter_membership_members"
        )
        fragments = filter_record._render(
            "website_membership_group.dynamic_filter_template_res_partner_grid",
            limit=16,
            search_domain=[("membership_group_member_ids.group_id", "=", group.id)],
        )
        # Should be empty because partner is not website_published
        self.assertFalse(any("Hidden Member" in f for f in fragments))
