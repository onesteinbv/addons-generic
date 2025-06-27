import freezegun

from odoo import fields
from odoo.tests import common


class TestMembershipTypeWizard(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        cls.group = cls.env["membership.group"].create({"name": "Group"})
        cls.member = cls.env["membership.group.member"].create(
            {
                "partner_id": cls.partner.id,
                "group_id": cls.group.id,
                "type": "follower",
                "date_from": "2025-01-01",
            }
        )

    def test_change_type_creates_new_member(self):
        with freezegun.freeze_time("2025-06-27"):
            wizard = self.env["membership.type.wizard"].create(
                {
                    "member_id": self.member.id,
                    "type": "collaborator",
                    "date_from": "2025-06-27",
                }
            )
            self.assertEqual(
                wizard.member_date_to,
                fields.Date.subtract(wizard.date_from),
            )

            values = wizard._prepare_new_member_line_values()
            self.assertEqual(values["partner_id"], self.partner.id)
            self.assertEqual(values["group_id"], self.group.id)
            self.assertEqual(values["type"], "collaborator")
            self.assertEqual(str(values["date_from"]), "2025-06-27")

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
            self.assertEqual(new_member.type, "collaborator")
            self.assertEqual(str(new_member.date_from), "2025-06-27")
