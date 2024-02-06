from odoo import fields, models


class IncomeTaxLog(models.TransientModel):
    _name = "l10n.nl.income.tax.log"
    _description = "Income Tax Log"

    report_id = fields.Many2one(comodel_name="l10n.nl.income.tax.report")
    currency_id = fields.Many2one(related="report_id.currency_id")

    type = fields.Selection(
        selection=[("factual", "Factual"), ("forecast", "Forecast")]
    )

    rule_id = fields.Many2one(comodel_name="l10n.nl.income.tax.rule")
    description = fields.Html(related="rule_id.description")
    deduction = fields.Monetary(currency_field="currency_id")
    taxable_income = fields.Monetary(currency_field="currency_id", string="Income")
    tax = fields.Monetary(currency_field="currency_id")
