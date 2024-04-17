# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    nc_calendar_ids = fields.One2many("nc.calendar", "user_id", "NextCloud Calendar")

    def setup_nc_sync_user(self):
        action = {
            "name": "Nextcloud User Setup",
            "view_mode": "form",
            "res_model": "nc.sync.user",
            "type": "ir.actions.act_window",
            "context": {"pop_up": True},
            "target": "new",
        }
        nc_sync_user_id = self.env["nc.sync.user"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )
        if nc_sync_user_id:
            action["res_id"] = nc_sync_user_id.id
        return action

    def sync_user_events(self):
        sync_users = self.env["nc.sync.user"].search(
            [("user_id", "=", self.id)], limit=1
        )
        if not sync_users:
            raise UserError("Sync User not found")
        elif sync_users and not sync_users.sync_calendar:
            raise UserError("Sync Calendar is not enabled for this User")
        self.env["nextcloud.caldav"].with_context({"per_user": self}).sync_cron()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": ("Nextcloud Sync"),
                "message": "Sync Done",
                "type": "success",
                "sticky": False,
            },
        }
