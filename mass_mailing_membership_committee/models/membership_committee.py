from odoo import fields, models


class MembershipCommittee(models.Model):
    _inherit = "membership.committee"

    mailing_list_id = fields.Many2one("mailing.list")
