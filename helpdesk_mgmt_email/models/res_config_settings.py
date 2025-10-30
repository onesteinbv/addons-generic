from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    helpdesk_mgmt_send_email_on_ticket_creation = fields.Boolean(
        related="company_id.helpdesk_mgmt_send_email_on_ticket_creation",
        readonly=False,
    )
