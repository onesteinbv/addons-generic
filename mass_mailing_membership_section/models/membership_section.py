from odoo import fields, models


class MembershipSection(models.Model):
    _inherit = "membership.section"

    mailing_list_id = fields.Many2one("mailing.list")
