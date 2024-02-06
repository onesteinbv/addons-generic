# Copyright 2020-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class CrmTeam(models.Model):
    _inherit = "crm.team"

    @api.model_create_multi
    def create(self, vals_list):
        if self.env["crm.team"].search([], limit=1):
            self._raise_no_active_sales_team()
        return super().create(vals_list)

    @api.constrains("active")
    def _check_one_active_sales_team(self):
        if not self.env["crm.team"].search([], limit=1):
            self._raise_one_active_active_sales_team()

    def _raise_no_active_sales_team(self):
        raise ValidationError(
            _("Sales Team already exists. Only one Sales Team is allowed.")
        )

    def _raise_one_active_active_sales_team(self):
        raise ValidationError(_("At least one Sales Team must be active."))
