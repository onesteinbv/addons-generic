# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).

from collections import defaultdict

from odoo import Command, api, fields, models


class AccountGroup(models.Model):
    _inherit = "account.group"
    _order = "code_prefix_start,sort_code"

    # FIXME: This should be English with Dutch translation
    referentiecode = fields.Char()
    code = fields.Char()
    sort_code = fields.Char(string="Sorting code")
    allowed_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        string="Saved Allowed Journals",
        help="Define in which journals this account can be used. If empty, can be used in all journals.",
    )
    active_allowed_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        string="Allowed Journals",
        help="This is the allowed journal for this group. It's calculated from all parent_groups",
        compute="_compute_active_allowed_journals",
        inverse="_inverse_active_allowed_journals",
    )
    auto_allowed_journals = fields.Boolean(
        string="Automatic Allowed Journals",
        default=True,
        help="If Automatic Allowed Journals is on. Changes here will be brought to the underlying accounts.",
    )
    rgs_allowed_journals_code = fields.Char(
        help="Comma reparated list of allowed journal codes."
    )
    rgs_allowed_journals_type = fields.Char(
        help="Comma reparated list of allowed journal types."
    )
    account_ids = fields.One2many(
        comodel_name="account.account",
        compute="_compute_account_ids",
        string="Accounts",
    )  # TODO: Move to account_usability

    @api.depends_context("company")
    @api.depends("code_prefix_start", "code_prefix_end")
    def _compute_account_ids(self):
        query = """
            SELECT
                a.id, g.id
            FROM
                account_account a
            JOIN
                account_group g
                ON g.code_prefix_start <= LEFT((a.code_store::json ->> %(company_id)s), char_length(g.code_prefix_start))
                AND g.code_prefix_end >= LEFT((a.code_store::json ->> %(company_id)s), char_length(g.code_prefix_end))
                AND g.company_id = %(company_id)s
            WHERE g.id IN %(group_ids)s
        """
        self.env.cr.execute(
            query,
            {
                "group_ids": tuple(self.ids),
                "company_id": str(self.env.company.root_id.id),
            },
        )
        res = self.env.cr.fetchall()
        group_accounts = defaultdict(list)
        for account_id, group_id in res:
            group_accounts[group_id].append(account_id)

        for group in self:
            group.account_ids = [Command.set(group_accounts[group.id])]

    @api.depends("parent_id", "parent_id.allowed_journal_ids", "allowed_journal_ids")
    @api.onchange("parent_id", "allowed_journal_ids")
    def _compute_active_allowed_journals(self):
        for rec in self:
            allowed_journals = rec.allowed_journal_ids
            if rec.parent_id:
                allowed_journals |= rec.parent_id.active_allowed_journal_ids
            rec.active_allowed_journal_ids = allowed_journals

    def _inverse_active_allowed_journals(self):
        for rec in self:
            parent_journals = rec.parent_id.active_allowed_journal_ids
            rec.allowed_journal_ids = rec.active_allowed_journal_ids - parent_journals

    def _adapt_parent_account_group(self, company=None):
        company = company if company else self.company_id
        if company.chart_template != "nl_rgs":
            return super(AccountGroup, self)._adapt_parent_account_group()

    def write(self, vals):
        ret = super().write(vals)
        self.accounts_set_allowed_journals()
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.accounts_set_allowed_journals()
        return records

    def accounts_set_allowed_journals(self):
        for rec in self.filtered(lambda g: g.auto_allowed_journals):
            rec.account_ids.group_set_allowed_journals()
