from odoo import fields, models


class MailingList(models.Model):
    _inherit = "mailing.list"

    membership_group_ids = fields.One2many("membership.group", "mailing_list_id")
