from odoo.tests import common


class TestMembershipGroup(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        membership_group_obj = cls.env["membership.group"]
        res_partner_obj = cls.env["res.partner"]
        membership_group_member_obj = cls.env["membership.group.member"]

        cls.group_1 = membership_group_obj.create({"name": "Test Group 1"})
        cls.group_2 = membership_group_obj.create({"name": "Test Group 2"})
        cls.partner_1 = res_partner_obj.create({"name": "Test partner 1"})
        cls.partner_2 = res_partner_obj.create({"name": "Test partner 2"})

        cls.membership_1a = membership_group_member_obj.create(
            {
                "partner_id": cls.partner_1.id,
                "group_id": cls.group_1.id,
            }
        )
        cls.membership_1b = membership_group_member_obj.create(
            {
                "partner_id": cls.partner_2.id,
                "group_id": cls.group_1.id,
            }
        )
        cls.membership_2a = membership_group_member_obj.create(
            {
                "partner_id": cls.partner_1.id,
                "group_id": cls.group_2.id,
            }
        )

    def test_01_membership_group_computed_fields(self):
        self.assertListEqual(
            self.group_1.partner_ids.ids, [self.partner_1.id, self.partner_2.id]
        )
        self.assertListEqual(self.group_2.partner_ids.ids, [self.partner_1.id])
        self.assertEqual(self.group_1.partner_ids_count, 2)
        self.assertEqual(self.group_2.partner_ids_count, 1)

    def test_02_partner_computed_fields(self):
        self.assertListEqual(
            self.partner_1.membership_group_ids.ids, [self.group_1.id, self.group_2.id]
        )
        self.assertListEqual(self.partner_2.membership_group_ids.ids, [self.group_1.id])
        self.assertEqual(self.partner_1.membership_group_ids_count, 2)
        self.assertEqual(self.partner_2.membership_group_ids_count, 1)

    def test_03_action_open_partner_view(self):
        res = self.group_1.action_open_partner_view()
        self.assertEqual(res["xml_id"], "membership.action_membership_members")
        self.assertEqual(
            res["domain"],
            "[('id','in',[" + ",".join(map(str, self.group_1.partner_ids.ids)) + "])]",
        )

        res = self.group_2.action_open_partner_view()
        self.assertEqual(
            res["views"], [(self.env.ref("base.view_partner_form").id, "form")]
        )
        self.assertEqual(res["res_id"], self.partner_1.id)

    def test_04_action_open_membership_group_view(self):
        res = self.partner_1.action_open_membership_group_view()
        self.assertEqual(res["xml_id"], "membership_group.membership_group_action")
        self.assertEqual(
            res["domain"],
            "[('id','in',["
            + ",".join(map(str, self.partner_1.membership_group_ids.ids))
            + "])]",
        )

        res = self.partner_2.action_open_membership_group_view()
        self.assertEqual(
            res["views"],
            [
                (
                    self.env.ref("membership_group.membership_group_view_form").id,
                    "form",
                )
            ],
        )
        self.assertEqual(res["res_id"], self.group_1.id)
