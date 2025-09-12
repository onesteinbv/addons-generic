from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    email = fields.Char(
        "Team Email", help="This would be used when sending out emails to contacts"
    )
