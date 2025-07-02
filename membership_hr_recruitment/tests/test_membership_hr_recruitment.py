from odoo.addons.base.tests.common import BaseCommon


class TestMembershipHrRecruitment(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            [{"name": "John", "login": "test1", "email": "john@test.com"}]
        )
        cls.candidate = cls.env["hr.candidate"].create(
            [{"partner_name": "John","partner_id": cls.user.partner_id.id,}]
        )
        cls.applicant_1 = cls.env["hr.applicant"].create(
            {
                "membership_applicant": True,
                "candidate_id": cls.candidate.id
            }
        )

    def test_01_default_values_for_employee_for_member_applicant(self):
        action = self.applicant_1.create_employee_from_applicant()
        self.assertEqual(action["context"]["default_employee_type"], "member")
        self.assertEqual(action["context"]["default_user_id"], self.user.id)

    def test_02_user_groups_for_member_employee_user(self):
        self.env["hr.employee"].create(
            {"name": "Mike", "employee_type": "member", "user_id": self.user.id}
        )
        self.assertIn(
            self.env["hr.employee"].get_member_groups()[0], self.user.groups_id.ids
        )
