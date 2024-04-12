# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class RunSyncWizard(models.TransientModel):
    _name = "run.sync.wizard"

    def run_sync_cron(self):
        self.env["nextcloud.caldav"].sync_cron()
