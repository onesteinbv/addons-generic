# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    priority = fields.Selection(selection_add=[('0', ''),
                                               ('1', 'Low'),
                                               ('2', 'Medium'),
                                               ('3', 'High'),
                                               ('4', 'Critical'),
                                               ('5', 'Blocker'),
                                               ], default="0", string="Priority")
