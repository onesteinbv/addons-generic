from ast import literal_eval

from odoo import fields, models
from odoo.tools.misc import format_date


class MembershipVoteHistory(models.TransientModel):
    _name = "membership.vote.history"
    _description = "Membership Vote History"

    voting_date = fields.Date(
        "Voting at Date",
        help="Choose a date to see the members who could vote at that date.",
        default=fields.Date.today,
    )

    def open_at_date(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "membership_group.action_membership_group_voting_member"
        )
        action["display_name"] = format_date(self.env, self.voting_date)
        action["context"] = dict(
            literal_eval(action["context"]),
            active_test=False,
            export_xlsx=True,
        )
        action["domain"] = [
            ("group_id.voting_group", "=", True),
            ("date_from", "<=", self.voting_date),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", self.voting_date),
        ]

        return action
