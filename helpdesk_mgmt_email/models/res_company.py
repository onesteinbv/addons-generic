# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    helpdesk_mgmt_use_team_email_as_reply_to = fields.Boolean(
        string="Use Helpdesk team's email as the reply to address in mail communications through chatter"
    )
