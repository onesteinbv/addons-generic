# Copyright 2026 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("digest_membership", "post_install", "-at_install")
class TestDigestMembership(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.digest = cls.env["digest.digest"].create(
            {
                "name": "Test Digest",
                "periodicity": "daily",
                "company_id": cls.company.id,
                "kpi_membership_new_members": True,
            }
        )

    def test_check_kpi_access(self):
        self.digest._check_kpi_access()

        with patch(
            "odoo.addons.base.models.res_users.Users.has_group",
            return_value=False,
        ):
            with self.assertRaises(AccessError):
                self.digest._check_kpi_access()

    def test_kpi_membership_new_members(self):
        with patch.object(
            type(self.env["res.partner"]),
            "search_count",
            return_value=1,
        ):
            self.digest._compute_kpi_membership_new_members_value()

            self.assertEqual(
                self.digest.kpi_membership_new_members_value,
                1,
            )
