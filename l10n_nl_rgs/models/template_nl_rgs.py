# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, Command
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('nl_rgs')
    def _get_nl_rgs_template_data(self):
        return {
            'name': 'Nederlands Referentie Grootboekschema',
            'code_digits': '7',
            'use_anglo_saxon': True,
            'property_account_receivable_id': 'recv',
            'property_account_payable_id': 'pay',
            'property_account_expense_categ_id': '7001010',
            'property_account_income_categ_id': '8001010',
            'property_stock_account_input_categ_id': '1210010',
            'property_stock_account_output_categ_id': '1104030',
            'property_stock_valuation_account_id': '3002010',
        }

    @template('nl_rgs', 'res.company')
    def _get_nl_rgs_res_company(self):
        return {
            self.env.company.id: {
                'account_fiscal_country_id': 'base.nl',
                'bank_account_code_prefix': '100201',
                'cash_account_code_prefix': '100101',
                'transfer_account_code_prefix': '100301',
                'account_default_pos_receivable_account_id': 'recv',
                'income_currency_exchange_account_id': '8407010',
                'expense_currency_exchange_account_id': '4210050',
                'account_journal_early_pay_discount_loss_account_id': '4210070',
                'account_journal_early_pay_discount_gain_account_id': '4210070',
                'account_journal_payment_debit_account_id': '1101050',
                'account_journal_payment_credit_account_id': '1203050',
                'default_cash_difference_income_account_id': '4210070',
                'default_cash_difference_expense_account_id': '4210070',
            },
        }

    @template('nl_rgs', 'account.reconcile.model')
    def _get_nl_rgs_reconcile_model(self):
        return {
            'prive_opname_template': {
                'name': 'Privé opname',
                'rule_type': 'writeoff_button',
                'line_ids': [
                    Command.create({
                        'account_id': '0509040',
                        'amount_string': '100',
                    }),
                ],
            },
            'prive_storting_template': {
                'name': 'Privé storting',
                'rule_type': 'writeoff_button',
                'line_ids': [
                    Command.create({
                        'account_id': '0509030',
                        'amount_string': '100',
                    }),
                ],
            },
            'kruisposten_template': {
                'name': 'Kruisposten',
                'rule_type': 'writeoff_button',
                'line_ids': [
                    Command.create({
                        'account_id': '1003010',
                        'amount_string': '100',
                    }),
                ],
            },
            'bankkosten_template': {
                'name': 'Bankkosten',
                'rule_type': 'writeoff_button',
                'line_ids': [
                    Command.create({
                        'account_id': '4210040',
                        'amount_string': '100',
                    }),
                ],
            },
            'verzekeringen_template': {
                'name': 'Verzekeringen',
                'rule_type': 'writeoff_button',
                'line_ids': [
                    Command.create({
                        'account_id': '4208020',
                        'amount_string': '100',
                    }),
                ],
            },
            'spaarrekening_template': {
                'name': 'Spaarrekening',
                'rule_type': 'writeoff_button',
                'line_ids': [
                    Command.create({
                        'account_id': '1002070',
                        'amount_string': '100',
                    }),
                ],
            },
        }
