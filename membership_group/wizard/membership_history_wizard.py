from ast import literal_eval

from odoo import fields, models
from odoo.osv import expression
from odoo.tools.misc import format_date


class MembershipHistoryWizard(models.TransientModel):
    _name = "membership.history.wizard"
    _description = "Membership History Wizard"

    date = fields.Date(
        help="Choose a date to see which member was active at that date.",
        default=fields.Date.today,
    )
    only_voting_members = fields.Boolean()
    group_ids = fields.Many2many("membership.group", string="Membership Groups")

    def open_at_date(self):
        self.ensure_one()
        domain = []
        if self.group_ids:
            domain = expression.AND([domain, [("group_id", "in", self.group_ids.ids)]])

        if self.only_voting_members:
            xml_name = "membership_group.action_membership_group_voting_member"
            domain = expression.AND([domain, [("group_id.voting_group", "=", True)]])
        else:
            xml_name = "membership_group.action_membership_group_member"

        action = self.env["ir.actions.act_window"]._for_xml_id(xml_name)
        action["display_name"] = format_date(self.env, self.date)
        action["context"] = dict(
            literal_eval(action["context"]),
            export_xlsx=True,
        )

        domain = expression.AND(
            [
                domain,
                [
                    ("date_from", "<=", self.date),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", self.date),
                ],
            ]
        )

        action["domain"] = domain

        return action
