# Copyright 2026 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("digest_membership_website_payment", "post_install", "-at_install")
class TestDigestMembershipWebsitePayment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.digest = cls.env["digest.digest"].create(
            {
                "name": "Test Digest Donations",
                "periodicity": "daily",
                "company_id": cls.company.id,
                "kpi_membership_donations": True,
                "kpi_membership_donations_amount": True,
            }
        )

        cls.provider = cls.env["payment.provider"].search([], limit=1)
        if not cls.provider:
            cls.provider = cls.env["payment.provider"].create(
                {
                    "name": "Test Provider",
                    "code": "none",
                    "company_id": cls.company.id,
                }
            )
        cls.payment_method = cls.env["payment.method"].search([], limit=1)
        if not cls.payment_method:
            cls.payment_method = cls.env["payment.method"].create(
                {
                    "name": "Test Method",
                    "code": "test_method",
                }
            )

        cls.partner_member = cls.env["res.partner"].create(
            {
                "name": "Member Partner",
                "free_member": True,
            }
        )

        cls.partner_non_member = cls.env["res.partner"].create(
            {
                "name": "Non Member Partner",
            }
        )

        cls.tx_member1 = cls.env["payment.transaction"].create(
            {
                "provider_id": cls.provider.id,
                "payment_method_id": cls.payment_method.id,
                "reference": "TX-MEMBER-1",
                "amount": 100.0,
                "currency_id": cls.company.currency_id.id,
                "partner_id": cls.partner_member.id,
                "is_donation": True,
                "state": "done",
            }
        )

        cls.tx_member2 = cls.env["payment.transaction"].create(
            {
                "provider_id": cls.provider.id,
                "payment_method_id": cls.payment_method.id,
                "reference": "TX-MEMBER-2",
                "amount": 200.0,
                "currency_id": cls.company.currency_id.id,
                "partner_id": cls.partner_member.id,
                "is_donation": True,
                "state": "done",
            }
        )

        cls.tx_non_member = cls.env["payment.transaction"].create(
            {
                "provider_id": cls.provider.id,
                "payment_method_id": cls.payment_method.id,
                "reference": "TX-NON-MEMBER-1",
                "amount": 50.0,
                "currency_id": cls.company.currency_id.id,
                "partner_id": cls.partner_non_member.id,
                "is_donation": True,
                "state": "done",
            }
        )

    def test_kpi_membership_donations_value(self):
        start = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        end = fields.Datetime.add(fields.Datetime.now(), days=1)
        with patch.object(
            type(self.digest),
            "_get_kpi_compute_parameters",
            return_value=(start, end, self.company),
        ):
            self.digest._compute_kpi_membership_donations_value()
            self.assertEqual(
                self.digest.kpi_membership_donations_value,
                2,
            )

    def test_kpi_membership_donations_amount_value(self):
        start = fields.Datetime.subtract(fields.Datetime.now(), days=1)
        end = fields.Datetime.add(fields.Datetime.now(), days=1)
        with patch.object(
            type(self.digest),
            "_get_kpi_compute_parameters",
            return_value=(start, end, self.company),
        ):
            self.digest._compute_kpi_membership_donations_amount_value()
            self.assertEqual(
                self.digest.kpi_membership_donations_amount_value,
                300.0,
            )
