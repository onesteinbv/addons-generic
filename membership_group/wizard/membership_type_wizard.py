from odoo import api, fields, models

from ..models.membership_group_member import MEMBER_TYPE


class MembershipTypeWizard(models.TransientModel):
    _name = "membership.type.wizard"
    _description = "Membership Type Wizard"

    member_id = fields.Many2one(
        "membership.group.member",
        string="Member",
        required=True,
        ondelete="cascade",
    )
    member_state = fields.Selection(related="member_id.state")
    member_current_type = fields.Selection(
        related="member_id.type",
        string="Current Type",
    )
    member_date_to = fields.Date(
        compute="_compute_member_date_to",
    )

    type = fields.Selection(MEMBER_TYPE)
    date_from = fields.Date(
        string="From",
        help="Start date of the membership",
        required=True,
    )

    @api.depends("date_from")
    def _compute_member_date_to(self):
        for record in self:
            record.member_date_to = fields.Date.subtract(record.date_from, days=1)

    def _prepare_new_member_line_values(self):
        self.ensure_one()
        return {
            "partner_id": self.member_id.partner_id.id,
            "group_id": self.member_id.group_id.id,
            "type": self.type,
            "date_from": self.date_from,
        }

    def action_change_type(self):
        rec_values = []
        for record in self:
            record.member_id.date_to = record.member_date_to
            if record.date_from <= fields.Date.context_today(record):
                record.member_id.date_end = record.member_date_to
            rec_values.append(record._prepare_new_member_line_values())

        if rec_values:
            self.env["membership.group.member"].create(rec_values)
