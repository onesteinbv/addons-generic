# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).

from odoo import api, fields, models


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
        inverse="_inverse_set_allowed_journals",
    )
    auto_allowed_journals = fields.Boolean(
        string="Automatic Allowed Journals",
        default=True,
        help="If Automatic Allowed Journals is on. Changes here will be brought to the underlying accounts.",
    )
    # From account financial report
    group_child_ids = fields.One2many(
        comodel_name="account.group", inverse_name="parent_id", string="Child Groups"
    )
    account_ids = fields.One2many(
        comodel_name="account.account", inverse_name="group_id", string="Accounts"
    )

    def _adapt_parent_account_group(self):
        if self.company_id.chart_template_id != self.env.ref(
            "l10n_nl_rgs.l10nnl_rgs_chart_template", False
        ):
            return super(AccountGroup, self)._adapt_parent_account_group()

    def get_all_account_ids(self):
        accounts = self.env["account.account"]
        for rec in self:
            accounts |= rec.account_ids
            if rec.group_child_ids:
                accounts |= rec.group_child_ids.get_all_account_ids()
        return accounts

    def get_all_allowed_journal_ids(self):
        allowed_journals = self.env["account.journal"]
        for rec in self:
            allowed_journals |= rec.allowed_journal_ids
            if rec.parent_id:
                allowed_journals |= rec.parent_id.get_all_allowed_journal_ids()
        return allowed_journals

    def write(self, vals):
        ret = super().write(vals)
        # Always check the allowed journals if auto_allowed_journals
        self.accounts_set_allowed_journals()
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.accounts_set_allowed_journals()
        return records

    def accounts_set_allowed_journals(self):
        for rec in self:
            if rec.auto_allowed_journals:
                rec.with_context(
                    group_allowed_journal_change=True
                ).account_ids.allowed_journal_ids = rec.active_allowed_journal_ids

    @api.depends("parent_id", "parent_id.allowed_journal_ids")
    @api.onchange("parent_id", "allowed_journal_ids")
    def _compute_active_allowed_journals(self):
        for rec in self:
            rec.active_allowed_journal_ids = rec.get_all_allowed_journal_ids()

    def _inverse_set_allowed_journals(self):
        for rec in self:
            parent_journals = rec.parent_id.get_all_allowed_journal_ids()
            rec.allowed_journal_ids = rec.active_allowed_journal_ids - parent_journals
