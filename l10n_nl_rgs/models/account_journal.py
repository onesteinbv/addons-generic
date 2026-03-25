# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).

from odoo import Command, _, api, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _prepare_liquidity_account_vals(self, company, code, vals):
        account_vals = super()._prepare_liquidity_account_vals(company, code, vals)

        if company.account_fiscal_country_id.code == "NL":
            account_vals.setdefault("tag_ids", [])
            account_vals["tag_ids"].append(
                (4, self.env.ref("l10n_nl_rgs.account_tag_1003000").id)
            )

        return account_vals

    @api.model
    def _fill_missing_values(self, vals, protected_codes=False):
        chart_template = self.env.company.chart_template
        is_rgs = chart_template == "nl_rgs"
        is_bank = vals.get("type") == "bank"
        is_cash = vals.get("type") == "cash"
        if not vals.get("default_account_id") and is_rgs and (is_bank or is_cash):
            account = self.env[
                "account.chart.template"
            ]._l10n_nl_rgs_get_create_bank_cash_account(vals["type"], self.env.company)
            if account:
                vals.update({"default_account_id": account.id})
                account.deprecated = False
            else:
                if is_bank:
                    raise ValidationError(_("Bank Account is required."))
                if is_cash:
                    raise ValidationError(_("Cash Account is required."))
        return super()._fill_missing_values(vals, protected_codes)

    @api.model_create_multi
    def create(self, vals_list):
        journals = super().create(vals_list)
        # When creating a new journal it should copy the allowed journal configuration from groups.
        # When loading the chart it is already done in the loading logic
        if self.env.context.get("chart_template_load"):
            return journals

        for journal in journals.filtered(
            lambda j: j.company_id.chart_template == "nl_rgs"
        ):
            subtype_code_mapping = {
                "general_wag": "WAG",
                "general_depr": "DEPR",
                "general_fcr": "FCR",
                "general_stj": "STJ",
                "general_tax": "TAX",
                "general_misc": "MISC",
                "general_exch": "EXCH",
            }
            journal_subtype_as_code = subtype_code_mapping.get(journal.subtype)
            groups = self.env["account.group"].search(
                [("company_id", "=", journal.company_id.id)]
            )
            for group in groups:
                if (
                    group.rgs_allowed_journals_type
                    and journal.type in group.rgs_allowed_journals_type.split(",")
                ):
                    group.allowed_journal_ids = [Command.link(journal.id)]
                if (
                    group.rgs_allowed_journals_code
                    and journal_subtype_as_code
                    in group.rgs_allowed_journals_code.split(",")
                ):
                    group.allowed_journal_ids = [Command.link(journal.id)]
            accounts = groups.mapped("account_ids")
            accounts.group_set_allowed_journals()
        return journals
