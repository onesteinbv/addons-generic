# Copyright 2026 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class Digest(models.Model):
    _inherit = "digest.digest"

    kpi_membership_activity = fields.Boolean("Activity")
    kpi_membership_activity_value = fields.Integer(
        compute="_compute_kpi_membership_activity_value"
    )

    def _compute_kpi_membership_activity_value(self):
        self._check_kpi_access()

        for record in self:
            start, end, company = record._get_kpi_compute_parameters()

            record.kpi_membership_activity_value = self.env[
                "membership.activity"
            ].search_count(
                [
                    ("date", ">=", start),
                    ("date", "<=", end),
                ]
            )
