from odoo import api, fields, models


class MembershipGroupMember(models.Model):
    _name = "membership.group.member"
    _description = "Membership Group Member"

    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Member",
        required=True,
        ondelete="cascade",
    )
    group_id = fields.Many2one("membership.group", required=True, ondelete="cascade")
    wants_to_collaborate = fields.Boolean()
    type = fields.Selection(
        [
            ("follower", "Follower"),
            ("applicant", "Applicant"),
            ("applicant_follower", "Applicant / Follower"),
            ("collaborator_follower", "Collaborator / Follower"),
            ("collaborator", "Collaborator"),
            ("committee", "Committee"),
        ],
    )
    date_from = fields.Date(
        default=fields.Date.context_today,
        help="Start date of the membership",
    )
    date_to = fields.Date(
        compute="_compute_date_to",
        store=True,
        readonly=False,
        precompute=True,
        help="Planned end date of the membership",
    )
    date_end = fields.Date(
        help="End date of the membership",
    )
    vote_right = fields.Boolean(
        compute="_compute_vote_right",
        store=True,
        help="Member has voting rights",
    )

    _sql_constraints = [
        (
            "partner_group_uniq",
            "unique(active, partner_id, group_id)",
            "Member already exists for this group!",
        )
    ]

    @api.depends("group_id")
    def _compute_date_to(self):
        for record in self:
            if (
                not record.date_to
                and record.group_id
                and record.group_id._has_termination_cycle()
            ):
                record.date_to = record.group_id.next_termination_date

    @api.depends("group_id")
    def _compute_vote_right(self):
        for record in self:
            record.vote_right = record.group_id.voting_group

    def action_revoke_membership(self):
        if active_records := self.filtered(lambda x: x.active):
            active_records.active = False
            active_records.date_end = fields.Date.today()
        return True

    @api.model
    def _cron_revoke_membership(self):
        self.search([("date_to", "<=", fields.date.today())]).action_revoke_membership()
