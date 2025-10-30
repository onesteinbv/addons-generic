from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    helpdesk_mgmt_send_email_on_ticket_creation = fields.Boolean(
        string="Send email on ticket creation"
    )
