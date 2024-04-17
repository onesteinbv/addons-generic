# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class NcEventStatus(models.Model):
    _name = "nc.event.status"
    _description = "Nextcloud Event Status"

    name = fields.Char("Nextcloud Status")
