from odoo import api, models


class AccountGroup(models.Model):
    _inherit = "account.group"

    def get_all_account_ids(self):
        accounts = self.env["account.account"]
        for rec in self:
            accounts |= rec.account_ids
            if rec.group_child_ids:
                accounts |= rec.group_child_ids.get_all_account_ids()
        return accounts

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        if self.company_id.chart_template != "nl_rgs":
            return super()._compute_complete_name()
        for group in self:
            group.complete_name = group.name

    @api.depends("code_prefix_start", "parent_id.complete_code", "code")
    def _compute_complete_code(self):
        if self.company_id.chart_template != "nl_rgs":
            return super()._compute_complete_code()
        for group in self:
            group.complete_code = group.code

    @api.depends(
        "code_prefix_start",
        "account_ids",
        "account_ids.code",
        "group_child_ids",
        "group_child_ids.account_ids.code",
        "code",
    )
    def _compute_group_accounts(self):
        if self.company_id.chart_template != "nl_rgs":
            return super()._compute_group_accounts()
        for group in self:
            gr_accounts = group.get_all_account_ids()
            group.compute_account_ids = [(6, 0, gr_accounts.ids)]
