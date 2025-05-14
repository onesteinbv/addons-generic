# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).

from odoo import Command, _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("nl_rgs")
    def _get_nl_rgs_template_data(self):
        return {
            "name": "Nederlands Referentie Grootboekschema",
            "code_digits": "7",
            "use_anglo_saxon": True,
            "property_account_receivable_id": "recv",
            "property_account_payable_id": "pay",
            "property_account_expense_categ_id": "7001010",
            "property_account_income_categ_id": "8001010",
            "property_stock_account_input_categ_id": "1210010",
            "property_stock_account_output_categ_id": "1104030",
            "property_stock_valuation_account_id": "3002010",
        }

    @template("nl_rgs", "res.company")
    def _get_nl_rgs_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.nl",
                "bank_account_code_prefix": "100201",
                "cash_account_code_prefix": "100101",
                "transfer_account_code_prefix": "100301",
                "account_default_pos_receivable_account_id": "recv",
                "income_currency_exchange_account_id": "8407010",
                "expense_currency_exchange_account_id": "4210050",
                "account_journal_early_pay_discount_loss_account_id": "4210070",
                "account_journal_early_pay_discount_gain_account_id": "4210070",
                "account_journal_payment_debit_account_id": "1101050",
                "account_journal_payment_credit_account_id": "1203050",
                "default_cash_difference_income_account_id": "4210070",
                "default_cash_difference_expense_account_id": "4210070",
                "transfer_account_id": "1003010",
            },
        }

    @template("nl_rgs", "account.reconcile.model")
    def _get_nl_rgs_reconcile_model(self):
        return {
            "prive_opname_template": {
                "name": "Privé opname",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": "0509040",
                            "amount_string": "100",
                        }
                    ),
                ],
            },
            "prive_storting_template": {
                "name": "Privé storting",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": "0509030",
                            "amount_string": "100",
                        }
                    ),
                ],
            },
            "kruisposten_template": {
                "name": "Kruisposten",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": "1003010",
                            "amount_string": "100",
                        }
                    ),
                ],
            },
            "bankkosten_template": {
                "name": "Bankkosten",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": "4210040",
                            "amount_string": "100",
                        }
                    ),
                ],
            },
            "verzekeringen_template": {
                "name": "Verzekeringen",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": "4208020",
                            "amount_string": "100",
                        }
                    ),
                ],
            },
            "spaarrekening_template": {
                "name": "Spaarrekening",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": "1002070",
                            "amount_string": "100",
                        }
                    ),
                ],
            },
        }

    @template("nl_rgs", "account.journal")
    def _get_nl_rgs_journal(self):
        data = {
            "accruals": {
                "name": _("Accruals"),
                "type": "general",
                "code": _("ACCR"),
                "show_on_dashboard": True,
                "color": 11,
                "sequence": 15,
                "subtype": "general_accr",
            },
            "depreciations": {
                "name": _("Depreciations"),
                "type": "general",
                "code": "DEPR",
                "show_on_dashboard": True,
                "color": 11,
                "sequence": 16,
                "subtype": "general_depr",
            },
            "foreign_currency_revaluation": {
                "name": _("Foreign currency revaluation"),
                "type": "general",
                "code": _("FCR"),
                "show_on_dashboard": True,
                "sequence": 17,
                "subtype": "general_fcr",
            },
            "wages": {
                "name": _("Wages"),
                "type": "general",
                "code": _("WAG"),
                "show_on_dashboard": True,
                "sequence": 18,
                "subtype": "general_wag",
            },
            "inventory_valuation": {
                "name": _("Inventory Valuation"),
                "type": "general",
                "code": _("STJ"),
                "show_on_dashboard": True,
                "sequence": 19,
                "subtype": "general_stj",
            },
            "taxes": {
                "name": _("Taxes"),
                "type": "general",
                "code": _("TAX"),
                "show_on_dashboard": True,
                "sequence": 20,
                "subtype": "general_tax",
            },
            "sale": {
                "name": _("Customer Invoices"),
                "type": "sale",
                "code": _("INV"),
                "show_on_dashboard": True,
                "color": 11,
                "sequence": 5,
            },
            "purchase": {
                "name": _("Vendor Bills"),
                "type": "purchase",
                "code": _("BILL"),
                "show_on_dashboard": True,
                "color": 11,
                "sequence": 6,
            },
            "general": {
                "name": _("Miscellaneous Operations"),
                "type": "general",
                "code": _("MISC"),
                "show_on_dashboard": False,
                "sequence": 9,
                "subtype": "general_misc",
            },
            "exch": {
                "name": _("Exchange Difference"),
                "type": "general",
                "code": _("EXCH"),
                "show_on_dashboard": False,
                "subtype": "general_exch",
            },
            "bank": {
                "name": _("Bank"),
                "type": "bank",
                "show_on_dashboard": True,
                "sequence": 7,
            },
            "cash": {
                "name": _("Cash"),
                "type": "cash",
                "show_on_dashboard": True,
            },
            "caba": {
                "name": _("Cash Basis Taxes"),
                "type": "general",
                "subtype": "general_misc",
                "code": _("CABA"),
                "show_on_dashboard": False,
                "active": False,
            },
        }
        return data

    def _post_load_data(
        self, template_code, company, template_data
    ):  # pylint: disable=missing-return
        super()._post_load_data(template_code, company, template_data)
        if template_code != "nl_rgs":
            return

        if cross_post_tag := self.env.ref(
            "l10n_nl_rgs.account_tag_1003000", raise_if_not_found=False
        ):
            company.account_journal_suspense_account_id.tag_ids += cross_post_tag
            company.account_journal_suspense_account_id.reconcile = True
            company.transfer_account_id.tag_ids += cross_post_tag
        if undist_profit_tag := self.env.ref(
            "l10n_nl_rgs.account_tag_0506009", raise_if_not_found=False
        ):
            company.get_unaffected_earnings_account().tag_ids += undist_profit_tag
        self._set_allowed_journals(company)

    def _set_allowed_journals(self, company):
        """Set the allowed journals for the group"""
        # NOTE: Migrated from 16 not sure why the subtype is not used directly like rgs_allowed_journals_subtype
        code_subtype_mapping = {
            "WAG": "general_wag",
            "DEPR": "general_depr",
            "FCR": "general_fcr",
            "STJ": "general_stj",
            "TAX": "general_tax",
            "MISC": "general_misc",
            "EXCH": "general_exch",
        }
        journals = self.env["account.journal"].search([("company_id", "=", company.id)])
        groups = self.env["account.group"].search([("company_id", "=", company.id)])

        for group in groups:
            allowed_journals = self.env["account.journal"]
            if group.rgs_allowed_journals_type:
                allowed_journals = journals.filtered_domain(
                    [
                        ("type", "in", group.rgs_allowed_journals_type.split(",")),
                    ]
                )
            if group.rgs_allowed_journals_code:
                codes = group.rgs_allowed_journals_code.split(",")
                allowed_subtypes = [
                    code_subtype_mapping[code]
                    for code in code_subtype_mapping.keys()
                    if code in codes
                ]
                allowed_journals |= journals.filtered_domain(
                    [("subtype", "in", allowed_subtypes)]
                )
            group.allowed_journal_ids = allowed_journals

        accounts = groups.mapped("account_ids")
        accounts.group_set_allowed_journals()

    def _l10n_nl_rgs_get_create_bank_cash_account(self, account_type, company):
        prefix = False
        if account_type == "bank" and company.bank_account_code_prefix:
            prefix = company.bank_account_code_prefix
        if account_type == "cash" and company.cash_account_code_prefix:
            prefix = company.cash_account_code_prefix
        template_data = self._get_nl_rgs_template_data()
        digits = int(template_data.get("code_digits"))
        accounts = self.env["account.account"].search(
            [("code", "=like", prefix + "%"), ("company_ids", "in", (company.id,))]
        )
        for num in range(0, 9):
            new_code = str(prefix.ljust(digits - 1, "0")) + str(num)
            rec = accounts.filtered(lambda a: a.code == new_code)
            if rec:
                existing_journal = self.env["account.journal"].search(
                    [
                        ("type", "=", account_type),
                        ("default_account_id", "=", rec.id),
                        ("company_id", "=", company.id),
                    ],
                    limit=1,
                )
                if not existing_journal:
                    return rec
            if not rec:
                # TODO automatically create a new account?
                # new_account = self.env["account.account"].create({"code": new_code, "company_id": company.id})
                # return new_account
                pass
