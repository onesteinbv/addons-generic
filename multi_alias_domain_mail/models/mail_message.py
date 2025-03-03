from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    record_alias_domain_id = fields.Many2one('mail.alias.domain', 'Alias Domain', ondelete='set null')
