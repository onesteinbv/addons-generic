# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields


class NcSyncError(models.Model):
    _name = "nc.sync.error"
    _description = "Nextcloud Sync Error"

    name = fields.Char()
    description = fields.Text()
    type = fields.Selection([("odoo", "Odoo"), ("nextcloud", "NextCloud")])
    severity = fields.Selection(
        [
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ]
    )
