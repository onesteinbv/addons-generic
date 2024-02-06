from odoo import fields, models


class MailingList(models.Model):
    _inherit = "mailing.list"

    section_ids = fields.One2many("membership.section", "mailing_list_id")
