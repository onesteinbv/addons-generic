# Copyright (C) 2016 Onestein (<http://www.onestein.eu>).

from odoo import Command, _, api, models

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
        if template_code == "nl_rgs":
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

    def _set_liquidity_transfer_account(self, company):
        """Set the transfer account 1003010 on the company (delete 1003011)"""
        # set account 1003010
        transfer_account = self.env["account.account"].search(
            [("code", "=", "1003010"), ("company_id", "=", company.id)], limit=1
        )
        if transfer_account and company.transfer_account_id != transfer_account:
            company.transfer_account_id = transfer_account

        # delete account 1003011
        wrong_transfer_account = self.env["account.account"].search(
            [("code", "=", "1003011"), ("company_id", "=", company.id)], limit=1
        )
        if (
            wrong_transfer_account
            and company.transfer_account_id != wrong_transfer_account
        ):
            wrong_transfer_account.unlink()

    def _set_liquidity_transfer_account_template(self):
        """Set liquidity transfer template: 1003010 (delete 1003011)"""
        rgs = self.env.ref("l10n_nl_rgs.l10nnl_rgs_chart_template")
        rgs_xml_id = "l10n_nl_rgs.l10nnl_rgs_chart_template_liquidity_transfer"
        liquidity_account_template = self.env.ref(rgs_xml_id, raise_if_not_found=False)
        if liquidity_account_template and liquidity_account_template.code == "1003011":
            # liquidity transfer account template
            correct_account_template = self.env["account.account.template"].search(
                [
                    ("code", "=", "1003010"),
                    ("chart_template_id", "=", rgs.id),
                ]
            )
            if len(correct_account_template) == 1:
                account_data = dict(
                    xml_id=rgs_xml_id,
                    record=correct_account_template,
                    noupdate=True,
                )
                self.env["ir.model.data"]._update_xmlids([account_data])
                liquidity_account_template.unlink()

    def add_account_group_allowed_journals(self, company):
        """Inherit this method to fix reference code missing in account groups"""
        self.ensure_one()

        group_templates = self.env["account.group.template"].search(
            [
                ("chart_template_id", "=", self.id),
                "|",
                ("rgs_allowed_journals_code", "!=", False),
                ("rgs_allowed_journals_type", "!=", False),
            ]
        )
        referentiecodes = group_templates.mapped("referentiecode")
        all_groups = self.env["account.group"].search(
            [("company_id", "=", company.id), ("referentiecode", "in", referentiecodes)]
        )
        all_journals = self.env["account.journal"].search(
            [
                ("company_id", "=", company.id),
            ]
        )

        for group_template in group_templates:
            group = all_groups.filtered(
                lambda g: g.referentiecode == group_template.referentiecode
            )
            if not group:
                continue
            journals = self.env["account.journal"]
            if group_template.rgs_allowed_journals_type:
                type_list = [
                    jtype
                    for jtype in group_template.rgs_allowed_journals_type.split(",")
                ]
                journals |= self.get_allowed_account_journals_based_on_type(
                    all_journals, type_list
                )
            if group_template.rgs_allowed_journals_code:
                code_list = [
                    jcode
                    for jcode in group_template.rgs_allowed_journals_code.split(",")
                ]
                journals |= self.get_allowed_account_journals_based_on_code(
                    all_journals, code_list
                )
            if journals:
                group.allowed_journal_ids = journals

        # Set the accounts allowed journal
        all_groups = self.env["account.group"].search([("company_id", "=", company.id)])
        for group in all_groups:
            group.accounts_set_allowed_journals()

    def get_allowed_account_journals_based_on_type(self, all_journals, type_list):
        return all_journals.filtered(lambda j: j.type in type_list)

    def get_allowed_account_journals_based_on_code(self, all_journals, code_list):
        subtype_mapping = {
            "WAG": "general_wag",
            "DEPR": "general_depr",
            "FCR": "general_fcr",
            "STJ": "general_stj",
            "TAX": "general_tax",
            "MISC": "general_misc",
            "EXCH": "general_exch",
        }
        subtype_list = []
        for k, v in subtype_mapping.items():
            if k in code_list and v not in subtype_list:
                subtype_list.append(v)
        return all_journals.filtered(lambda j: j.subtype in subtype_list)

    def _create_bank_journals(self, company, acc_template_ref):
        self.ensure_one()
        if self != self.env.ref("l10n_nl_rgs.l10nnl_rgs_chart_template", False):
            return super()._create_bank_journals(company, acc_template_ref)

        bank_journals = self.env["account.journal"]
        # Create the journals that will trigger the account.account creation
        for acc in self._get_default_bank_journals_data():
            vals = {
                "name": acc["acc_name"],
                "type": acc["account_type"],
                "company_id": company.id,
                "currency_id": acc.get("currency_id", self.env["res.currency"]).id,
                "sequence": 10,
            }
            # Bank/cash
            account = self._l10n_nl_rgs_get_create_bank_cash_account(
                acc["account_type"], company
            )
            if account:
                vals.update({"default_account_id": account.id})
                account.deprecated = False
            new_journal = self.env["account.journal"].create(vals)
            bank_journals += new_journal
            if account:
                account.allowed_journal_ids |= new_journal

        return bank_journals

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

    @api.model
    def _create_cash_discount_loss_account(self, company, code_digits):
        rgs_coa = self.env.ref("l10n_nl_rgs.l10nnl_rgs_chart_template", False)
        if (
            company.chart_template_id == rgs_coa
            and company.default_cash_difference_expense_account_id
        ):
            return company.default_cash_difference_expense_account_id
        return super()._create_cash_discount_loss_account(company, code_digits)

    @api.model
    def _create_cash_discount_gain_account(self, company, code_digits):
        rgs_coa = self.env.ref("l10n_nl_rgs.l10nnl_rgs_chart_template", False)
        if (
            company.chart_template_id == rgs_coa
            and company.default_cash_difference_income_account_id
        ):
            return company.default_cash_difference_income_account_id
        return super()._create_cash_discount_gain_account(company, code_digits)

    @api.model
    def _patch_fix_stock_account(self):
        # Installing stock_account will create ir.property property_stock_account_output_categ_id and property_stock_account_input_categ_id for the
        # main_company. Somehow if this module is installed it removes the ir.model.data or ir.property. (in rgs._load(main_company) -> self.generate_properties())
        # See: accounts/chart_template.py in def _load(self, company) it deletes ir.property
        # This is a core issue it can also be triggered by creating a database installing stock_account installing belgium coa switch to it, and update stock_account

        # TODO: Fix in core
        is_stock_account_module_installed = (
            self.env["ir.module.module"]
            .sudo()
            .search(
                [
                    ("name", "=", "stock_account"),
                    ("state", "=", "installed"),
                ]
            )
        )
        if is_stock_account_module_installed:
            xml_ids = [
                ("stock_account", "property_stock_account_output_categ_id"),
                ("stock_account", "property_stock_account_input_categ_id"),
            ]

            main_company = self.env.ref("base.main_company", False)
            for xml_id in xml_ids:
                ir_property = self.env.ref("%s.%s" % (xml_id[0], xml_id[1]), False)
                if ir_property:
                    continue
                self.env["ir.model.data"].create(
                    {
                        "res_id": self.env["ir.property"].search(
                            [
                                ("name", "=", xml_id[1]),
                                ("company_id", "=", main_company.id),
                                ("res_id", "=", False),
                            ]
                        ),
                        "model": "ir.property",
                        "name": xml_id[1],
                        "module": xml_id[0],
                        "noupdate": True,
                    }
                )
