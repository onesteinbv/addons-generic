# Copyright 2026 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models
from odoo.exceptions import AccessError


class Digest(models.Model):
    _inherit = "digest.digest"

    kpi_membership_new_members = fields.Boolean("New Members")
    kpi_membership_new_members_value = fields.Integer(
        compute="_compute_kpi_membership_new_members_value"
    )

    def _check_kpi_access(self):
        if not self.env.user.has_group("base.group_user"):
            raise AccessError(_("You do not have access to compute this KPI."))

    def _compute_kpi_membership_new_members_value(self):
        self._check_kpi_access()

        for record in self:
            start, end, company = record._get_kpi_compute_parameters()

            record.kpi_membership_new_members_value = self.env[
                "res.partner"
            ].search_count(
                [
                    ("company_id", "=", company.id),
                    ("membership_start", ">=", fields.Date.to_date(start)),
                    ("membership_start", "<=", fields.Date.to_date(end)),
                ]
            )
