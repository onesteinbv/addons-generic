# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    alias_domain_id = fields.Many2one(
        'mail.alias.domain', 'Alias Domain',
        readonly=False, related='company_id.alias_domain_id',
        help="If you have setup a catch-all email domain redirected to the Odoo server, enter the domain name here.")
