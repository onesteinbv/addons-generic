# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class NcCalendar(models.Model):
    _name = "nc.calendar"
    _description = "Nextcloud Calendar"

    name = fields.Char(string="Calendar", required=True)
    user_id = fields.Many2one(
        "res.users", string="User", ondelete="cascade", required=True
    )
    calendar_url = fields.Text(string="Calendar URL")

    @api.model
    def create(self, vals):
        if not self._context.get("sync", False):
            if "user_id" not in vals:
                vals["user_id"] = self.env.user.id
        return super(NcCalendar, self).create(vals)
