from odoo import fields, models


class MembershipGroup(models.Model):
    _inherit = "membership.group"

    mailing_list_id = fields.Many2one("mailing.list")
