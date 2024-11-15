from odoo.tests import common


class TestMembershipHr(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        membership_group_obj = cls.env["membership.group"]
        hr_department_obj = cls.env["hr.department"]

        cls.group_1 = membership_group_obj.create({"name": "Test Group 1"})
        cls.group_2 = membership_group_obj.create({"name": "Test Group 2"})
        cls.hr_department_1 = hr_department_obj.create({"name": "Test Department 1"})
        cls.hr_department_2 = hr_department_obj.create({"name": "Test Department 2"})

    def test_01_membership_hr(self):
        self.group_1.department_ids = [
            (6, 0, [self.hr_department_1.id, self.hr_department_2.id])
        ]
        self.assertEqual(self.group_1.department_id, self.hr_department_1)
        self.group_1.department_id = self.hr_department_2.id
        self.assertEqual(self.hr_department_2.membership_group_id, self.group_1)
        self.group_2.department_id = self.hr_department_1.id
        self.assertEqual(self.hr_department_1.membership_group_id, self.group_2)
