# Copyright 2026 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class Digest(models.Model):
    _inherit = "digest.digest"

    kpi_membership_donations = fields.Boolean("Donation")
    kpi_membership_donations_value = fields.Integer(
        compute="_compute_kpi_membership_donations_value"
    )

    kpi_membership_donations_amount = fields.Boolean(
        "Donation Amount",
        compute="_compute_kpi_membership_donations_amount",
    )
    kpi_membership_donations_amount_value = fields.Monetary(
        compute="_compute_kpi_membership_donations_amount_value",
        currency_field="currency_id",
    )

    def _get_donation_domain(self, company, start, end):
        return [
            ("company_id", "=", company.id),
            ("create_date", ">=", start),
            ("create_date", "<=", end),
            ("state", "=", "done"),
            ("is_donation", "=", True),
            ("partner_id.membership_state", "!=", "none"),
        ]

    def _compute_kpi_membership_donations_amount(self):
        for record in self:
            record.kpi_membership_donations_amount = record.kpi_membership_donations

    def _compute_kpi_membership_donations_amount_value(self):
        self._check_kpi_access()

        payment_transaction = self.env["payment.transaction"]

        for record in self:
            start, end, company = record._get_kpi_compute_parameters()

            domain = self._get_donation_domain(company, start, end)
            transactions = payment_transaction.search(domain)

            record.kpi_membership_donations_amount_value = sum(
                transactions.mapped("amount")
            )

    def _compute_kpi_membership_donations_value(self):
        self._check_kpi_access()

        payment_transaction = self.env["payment.transaction"]

        for record in self:
            start, end, company = record._get_kpi_compute_parameters()

            domain = self._get_donation_domain(company, start, end)

            record.kpi_membership_donations_value = payment_transaction.search_count(
                domain
            )
