# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    helpdesk_mgmt_use_team_email_as_reply_to = fields.Boolean(
        related="company_id.helpdesk_mgmt_use_team_email_as_reply_to",
        readonly=False,
    )
