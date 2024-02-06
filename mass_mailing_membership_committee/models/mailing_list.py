from odoo import fields, models


class MailingList(models.Model):
    _inherit = "mailing.list"

    committee_id = fields.One2many("membership.committee", "mailing_list_id")
