from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("de_skr49")
    def _get_de_skr49_template_data(self):
        return {
            "name": "Deutscher Kontenplan SKR49",
            "code_digits": "4",
            "property_account_receivable_id": "chart_skr49_0652",
            "property_account_payable_id": "chart_skr49_1346",
            "property_account_expense_categ_id": "chart_skr49_8154",
            "property_account_income_categ_id": "chart_skr49_8030",
        }

    @template("de_skr49", "res.company")
    def _get_de_skr49_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.de",
                "bank_account_code_prefix": "0920",
                "cash_account_code_prefix": "0945",
                "transfer_account_code_prefix": "0705",
                "income_currency_exchange_account_id": "chart_skr49_4154",
                "expense_currency_exchange_account_id": "chart_skr49_4715",
            },
        }
