import freezegun

from odoo import fields
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestMembershipGroup(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        membership_group_obj = cls.env["membership.group"]
        res_partner_obj = cls.env["res.partner"]
        membership_group_member_obj = cls.env["membership.group.member"]

        cls.group_1 = membership_group_obj.create([{"name": "Test Group 1"}])
        cls.group_2 = membership_group_obj.create([{"name": "Test Group 2"}])
        cls.partner_1 = res_partner_obj.create([{"name": "Test partner 1"}])
        cls.partner_2 = res_partner_obj.create([{"name": "Test partner 2"}])

        cls.membership_1a = membership_group_member_obj.create(
            [
                {
                    "partner_id": cls.partner_1.id,
                    "group_id": cls.group_1.id,
                    "date_from": fields.Date.today(),
                }
            ]
        )
        cls.membership_1b = membership_group_member_obj.create(
            [
                {
                    "partner_id": cls.partner_2.id,
                    "group_id": cls.group_1.id,
                    "date_from": fields.Date.today(),
                }
            ]
        )
        cls.membership_2a = membership_group_member_obj.create(
            [
                {
                    "partner_id": cls.partner_1.id,
                    "group_id": cls.group_2.id,
                    "date_from": fields.Date.today(),
                }
            ]
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

    def test_05_membership_group_with_revoke_date(self):
        group_1_with_termination = self.env["membership.group"].create(
            [
                {
                    "name": "Test Group 1 with termination",
                    "membership_end_date": "2055-06-01",
                }
            ]
        )
        member_group_termination = self.env["membership.group.member"].create(
            [
                {
                    "partner_id": self.partner_1.id,
                    "group_id": group_1_with_termination.id,
                    "date_from": "2025-01-01",
                }
            ]
        )

        self.assertEqual(
            member_group_termination.date_to,
            group_1_with_termination.membership_end_date,
        )
        self.assertEqual(member_group_termination.state, "current")

        with freezegun.freeze_time("2025-05-01"):
            self.env["membership.group.member"]._cron_revoke_membership()

        self.assertEqual(member_group_termination.state, "current")

        with freezegun.freeze_time("2025-06-01"):
            self.env["membership.group.member"]._cron_revoke_membership()

        self.assertEqual(member_group_termination.state, "historic")
        self.assertEqual(
            str(member_group_termination.date_end),
            "2055-06-01",
        )

    def test_06_overlap_dates(self):
        MembershipGroupMember = self.env["membership.group.member"]
        new_partner = self.env["res.partner"].create([{"name": "Test partner 3"}])
        member_1 = MembershipGroupMember.create(
            [
                {
                    "partner_id": new_partner.id,
                    "group_id": self.group_1.id,
                    "date_from": "2025-01-01",
                }
            ]
        )

        with self.assertRaises(ValidationError):
            MembershipGroupMember.create(
                [
                    {
                        "partner_id": new_partner.id,
                        "group_id": self.group_1.id,
                        "date_from": "2025-02-01",
                    }
                ]
            )

        with self.assertRaises(ValidationError):
            MembershipGroupMember.create(
                [
                    {
                        "partner_id": new_partner.id,
                        "group_id": self.group_1.id,
                        "date_from": "2025-01-02",
                    }
                ]
            )

        member_1.date_end = "2025-01-31"
        MembershipGroupMember.create(
            [
                {
                    "partner_id": new_partner.id,
                    "group_id": self.group_1.id,
                    "date_from": "2025-02-01",
                }
            ]
        )

        MembershipGroupMember.create(
            [
                {
                    "partner_id": new_partner.id,
                    "group_id": self.group_1.id,
                    "date_from": "2024-01-01",
                    "date_end": "2024-04-01",
                }
            ]
        )

        with self.assertRaises(ValidationError):
            MembershipGroupMember.create(
                [
                    {
                        "partner_id": new_partner.id,
                        "group_id": self.group_1.id,
                        "date_from": "2024-03-01",
                        "date_end": "2024-03-05",
                    }
                ]
            )

    def test_07_current_members(self):
        MembershipGroupMember = self.env["membership.group.member"]
        new_partner = self.env["res.partner"].create([{"name": "Test partner"}])
        MembershipGroupMember.create(
            [
                {
                    "partner_id": new_partner.id,
                    "group_id": self.group_1.id,
                    "date_from": "2024-01-01",
                }
            ]
        )
        with self.assertRaises(ValidationError):
            MembershipGroupMember.create(
                [
                    {
                        "partner_id": new_partner.id,
                        "group_id": self.group_1.id,
                        "date_from": "2024-01-01",
                    }
                ]
            )

    def test_08_compute_state_historic_with_date_to_date_end(self):
        MembershipGroupMember = self.env["membership.group.member"]
        member_group = self.env["membership.group"].create([{"name": "Just a group"}])

        with freezegun.freeze_time("2023-01-01"):
            member = MembershipGroupMember.create(
                [
                    {
                        "partner_id": self.partner_1.id,
                        "group_id": member_group.id,
                        "date_from": "2025-01-01",
                        "date_to": "2026-01-01",
                    }
                ]
            )
            self.assertEqual(member.state, "future")

        with freezegun.freeze_time("2025-01-01"):
            MembershipGroupMember._cron_process_membership()
            self.assertEqual(member.state, "current")

        with freezegun.freeze_time("2025-05-01"):
            MembershipGroupMember._cron_process_membership()
            self.assertEqual(member.state, "current")

        with freezegun.freeze_time("2025-06-01"):
            MembershipGroupMember._cron_process_membership()
            self.assertEqual(member.state, "current")

        member.date_end = "2025-07-1"
        with freezegun.freeze_time("2025-07-01"):
            MembershipGroupMember._cron_process_membership()
            self.assertEqual(member.state, "historic")
