# Copyright 2026 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("digest_membership_activity", "post_install", "-at_install")
class TestDigestMembershipActivity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.digest = cls.env["digest.digest"].create(
            {
                "name": "Test Digest Activity",
                "periodicity": "daily",
                "company_id": cls.company.id,
                "kpi_membership_activity": True,
            }
        )

    def test_kpi_membership_activity_value(self):
        with patch.object(
            type(self.env["membership.activity"]),
            "search_count",
            return_value=3,
        ):
            self.digest._compute_kpi_membership_activity_value()

            self.assertEqual(
                self.digest.kpi_membership_activity_value,
                3,
            )
