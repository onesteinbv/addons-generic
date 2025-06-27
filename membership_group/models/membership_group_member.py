from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MEMBER_TYPE = [
    ("follower", "Follower"),
    ("applicant", "Applicant"),
    ("applicant_follower", "Applicant / Follower"),
    ("collaborator_follower", "Collaborator / Follower"),
    ("collaborator", "Collaborator"),
    ("committee", "Committee"),
]


class MembershipGroupMember(models.Model):
    _name = "membership.group.member"
    _description = "Membership Group Member"
    _order = "state asc, date_from desc"

    state = fields.Selection(
        [
            ("current", "Current"),
            ("historic", "Historic"),
            ("future", "Future"),
        ],
        default="current",
        compute="_compute_state",
        precompute=True,
        store=True,
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Member",
        required=True,
        ondelete="cascade",
    )
    group_id = fields.Many2one("membership.group", required=True, ondelete="cascade")
    wants_to_collaborate = fields.Boolean()
    type = fields.Selection(MEMBER_TYPE)
    date_from = fields.Date(
        string="From",
        required=True,
        default=fields.Date.context_today,
        help="Start date of the membership",
    )
    date_to = fields.Date(
        string="To",
        compute="_compute_date_to",
        store=True,
        readonly=False,
        precompute=True,
        help="Planned end date of the membership",
    )
    date_end = fields.Date(
        string="Ended on",
        help="End date of the membership",
    )
    vote_right = fields.Boolean(
        compute="_compute_vote_right",
        store=True,
        help="Member has voting rights",
    )

    def _prepare_error_message(self):
        self.ensure_one()
        return _(
            "The member %(partner)s from group %(group)s",
            partner=self.partner_id.name,
            group=self.group_id.name,
        )

    @api.constrains("partner_id", "group_id", "date_from", "date_end", "date_to")
    def _check_no_overlap_dates(self):
        errors = []
        for record in self:
            message = record._prepare_error_message()
            if record.date_end and record.date_end < record.date_from:
                message += _(
                    " has an end date (%(date_end)s) that is before "
                    "the start date (%(date_from)s).",
                    date_end=record.date_end,
                    date_from=record.date_from,
                )
                errors.append(message)
            if record.date_to and record.date_to < record.date_from:
                message += _(
                    " has a date to (%(date_to)s) that is before "
                    "the start date (%(date_from)s).",
                    date_to=record.date_to,
                    date_from=record.date_from,
                )
                errors.append(message)
            if record.date_end and record.date_to and record.date_end > record.date_to:
                message += _(
                    " has an end date (%(date_end)s) that is after "
                    "the date to (%(date_to)s).",
                    date_end=record.date_end,
                    date_to=record.date_to,
                )
                errors.append(message)

            domain = [
                ("id", "!=", record.id),
                ("partner_id", "=", record.partner_id.id),
                ("group_id", "=", record.group_id.id),
            ]
            if records := self.search(domain):
                if error := records._check_overlap_dates(record):
                    message = record._prepare_error_message()
                    errors.append(message + error)

        if errors:
            raise ValidationError(
                _(
                    "Some membership records have errors:\n%(errors)s",
                    errors="\n".join(errors),
                )
            )

    @api.depends("date_from", "date_end", "date_to")
    def _compute_state(self):
        for record in self:
            today = fields.Date.context_today(record)

            if today < record.date_from:
                record.state = "future"
            elif record.date_end and record.date_end <= today:
                record.state = "historic"
            else:
                record.state = "current"

    def _check_overlap_dates(self, record):
        for rec in self:
            if rec.state == "current" and record.state == "current":
                return _(" has two current memberships in the same group!")

            if rec.state == "historic":
                continue

            rec_date_end = rec.date_end or rec.date_to
            record_date_end = record.date_end or record.date_to

            if (
                rec.date_from >= record.date_from
                and not rec_date_end
                and not record_date_end
            ):
                return _(" has dates overlap with an existing record!")
            elif (
                rec.date_from >= record.date_from
                and record_date_end
                and record_date_end > rec.date_from
            ):
                return _(" the membership dates overlap with an existing record!")
            elif record.date_from >= rec.date_from and (
                not rec_date_end or record.date_from <= rec_date_end
            ):
                return _(" the membership dates overlap with an existing record!")

    @api.depends("group_id")
    def _compute_date_to(self):
        for record in self:
            if (
                not record.date_to
                and record.group_id
                and record.group_id.membership_end_date
            ):
                record.date_to = record.group_id.membership_end_date

    @api.depends("group_id")
    def _compute_vote_right(self):
        for record in self:
            record.vote_right = record.group_id.voting_group

    def action_change_type(self):
        ref_name = "membership_group.action_membership_type_wizard"
        action = self.env["ir.actions.act_window"]._for_xml_id(ref_name)
        wizard = self.env["membership.type.wizard"].create(
            {
                "member_id": self.id,
                "date_from": self.date_to or fields.Date.today(),
            }
        )
        action["res_id"] = wizard.id
        ctx = dict(self.env.context) | {
            "create": True,
            "edit": True,
        }
        action["context"] = ctx
        return action

    def action_revoke_membership(self):
        self.state = "historic"
        self.date_end = fields.Date.today()

    def action_activate_membership(self):
        self.state = "current"

    def action_open_partners(self):
        ref_name = "membership.action_membership_members"
        action = self.env["ir.actions.act_window"]._for_xml_id(ref_name)
        action["context"] = {"active_test": False}
        if len(self.partner_id) > 1:
            action["domain"] = [("id", "in", self.partner_id.ids)]
        elif len(self.partner_id) == 1:
            action["views"] = [(False, "form")]
            action["res_id"] = self.partner_id.id
        return action

    @api.model
    def _cron_process_membership(self):
        today = fields.Date.context_today(self)
        self.search(
            [
                ("state", "=", "current"),
                "|",
                ("date_to", "<=", today),
                ("date_end", "<=", today),
            ]
        ).action_revoke_membership()
        self.search(
            [
                ("state", "=", "future"),
                ("date_from", "<=", today),
            ]
        ).action_activate_membership()
