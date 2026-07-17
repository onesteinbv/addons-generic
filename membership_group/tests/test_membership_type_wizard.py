import freezegun

from odoo import fields
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestMembershipTypeWizard(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.MemberType = cls.env["membership.group.member.type"]
        cls.type_follower = cls.MemberType.create([{"name": "Follower"}])
        cls.type_collaborator = cls.MemberType.create([{"name": "Collaborator"}])

        cls.partner = cls.env["res.partner"].create([{"name": "Partner"}])
        cls.group = cls.env["membership.group"].create([{"name": "Group"}])
        cls.member = cls.env["membership.group.member"].create(
            [
                {
                    "partner_id": cls.partner.id,
                    "group_id": cls.group.id,
                    "type_ids": [(6, 0, cls.type_follower.ids)],
                    "date_from": "2025-01-01",
                }
            ]
        )

    def test_01_member_current_type_ids_related_field(self):
        wizard = self.env["membership.type.wizard"].create(
            [
                {
                    "member_id": self.member.id,
                    "type_ids": [(6, 0, self.type_collaborator.ids)],
                    "date_from": "2025-06-27",
                }
            ]
        )
        self.assertEqual(wizard.member_current_type_ids, self.type_follower)
        self.assertEqual(wizard.member_group_id, self.group)
        self.assertEqual(wizard.member_state, self.member.state)

    def test_02_compute_member_date_to(self):
        wizard = self.env["membership.type.wizard"].create(
            [
                {
                    "member_id": self.member.id,
                    "type_ids": [(6, 0, self.type_collaborator.ids)],
                    "date_from": "2025-06-27",
                }
            ]
        )
        self.assertEqual(wizard.member_date_to, wizard.date_from)
        self.assertEqual(str(wizard.member_date_to), "2025-06-27")

        wizard.date_from = "2025-07-01"
        self.assertEqual(wizard.member_date_to, fields.Date.from_string("2025-07-01"))

    def test_03_prepare_new_member_line_values(self):
        wizard = self.env["membership.type.wizard"].create(
            [
                {
                    "member_id": self.member.id,
                    "type_ids": [(6, 0, self.type_collaborator.ids)],
                    "date_from": "2025-06-27",
                }
            ]
        )
        values = wizard._prepare_new_member_line_values()
        self.assertEqual(values["partner_id"], self.partner.id)
        self.assertEqual(values["group_id"], self.group.id)
        self.assertEqual(values["type_ids"], [(6, 0, self.type_collaborator.ids)])
        self.assertEqual(str(values["date_from"]), "2025-06-27")
        self.assertEqual(values["date_to"], self.member.date_to)

    def test_04_change_type_creates_new_member(self):
        with freezegun.freeze_time("2025-06-27"):
            wizard = self.env["membership.type.wizard"].create(
                [
                    {
                        "member_id": self.member.id,
                        "type_ids": [(6, 0, self.type_collaborator.ids)],
                        "date_from": "2025-06-27",
                    }
                ]
            )
            self.assertEqual(wizard.member_date_to, wizard.date_from)

            wizard.action_change_type()

            self.assertEqual(self.member.date_end, wizard.member_date_to)
            self.assertEqual(self.member.state, "historic")

            new_member = self.env["membership.group.member"].search(
                [
                    ("partner_id", "=", self.partner.id),
                    ("group_id", "=", self.group.id),
                ],
                order="id desc",
                limit=1,
            )
            self.assertEqual(new_member.type_ids, self.type_collaborator)
            self.assertEqual(str(new_member.date_from), "2025-06-27")

    def test_05_change_type_with_multiple_new_types(self):
        with freezegun.freeze_time("2025-06-27"):
            new_types = self.type_follower + self.type_collaborator
            wizard = self.env["membership.type.wizard"].create(
                [
                    {
                        "member_id": self.member.id,
                        "type_ids": [(6, 0, new_types.ids)],
                        "date_from": "2025-06-27",
                    }
                ]
            )
            wizard.action_change_type()

            new_member = self.env["membership.group.member"].search(
                [
                    ("partner_id", "=", self.partner.id),
                    ("group_id", "=", self.group.id),
                ],
                order="id desc",
                limit=1,
            )
            self.assertEqual(new_member.type_ids, new_types)

    def test_06_action_change_type_raises_for_future_date(self):
        with freezegun.freeze_time("2025-06-27"):
            wizard = self.env["membership.type.wizard"].create(
                [
                    {
                        "member_id": self.member.id,
                        "type_ids": [(6, 0, self.type_collaborator.ids)],
                        "date_from": "2025-06-28",
                    }
                ]
            )
            with self.assertRaises(ValidationError):
                wizard.action_change_type()

    def test_07_action_change_type_sets_member_date_end_when_due_today(self):
        # date_from equal to today: member.date_end must be updated (boundary case)
        with freezegun.freeze_time("2025-06-27"):
            wizard = self.env["membership.type.wizard"].create(
                [
                    {
                        "member_id": self.member.id,
                        "type_ids": [(6, 0, self.type_collaborator.ids)],
                        "date_from": "2025-06-27",
                    }
                ]
            )
            wizard.action_change_type()
            self.assertTrue(self.member.date_end)
            self.assertEqual(str(self.member.date_end), "2025-06-27")

    def test_08_action_change_type_multi_record(self):
        second_member = self.env["membership.group.member"].create(
            [
                {
                    "partner_id": self.env["res.partner"]
                    .create([{"name": "Partner 2"}])
                    .id,
                    "group_id": self.group.id,
                    "type_ids": [(6, 0, self.type_follower.ids)],
                    "date_from": "2025-01-01",
                }
            ]
        )
        with freezegun.freeze_time("2025-06-27"):
            wizard_1 = self.env["membership.type.wizard"].create(
                {
                    "member_id": self.member.id,
                    "type_ids": [(6, 0, self.type_collaborator.ids)],
                    "date_from": "2025-06-27",
                }
            )
            wizard_2 = self.env["membership.type.wizard"].create(
                {
                    "member_id": second_member.id,
                    "type_ids": [(6, 0, self.type_collaborator.ids)],
                    "date_from": "2025-06-27",
                }
            )
            (wizard_1 + wizard_2).action_change_type()

            self.assertEqual(self.member.state, "historic")
            self.assertEqual(second_member.state, "historic")

            new_members = self.env["membership.group.member"].search(
                [
                    ("group_id", "=", self.group.id),
                    ("type_ids", "in", self.type_collaborator.ids),
                ]
            )
            self.assertEqual(len(new_members), 2)
