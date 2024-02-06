from datetime import datetime

from odoo import _, api, fields, models


class IncomeTaxReport(models.TransientModel):
    _name = "l10n.nl.income.tax.report"
    _description = "Income Tax Report"

    # Options
    year_id = fields.Many2one(comodel_name="l10n.nl.income.tax.year")
    prepaid_tax_account_id = fields.Many2one(comodel_name="account.account")
    domain = fields.Selection(
        string="Use",
        required=True,
        selection=[("account_move_line", "Journal Items")],
        default="account_move_line",
    )

    currency_id = fields.Many2one(related="year_id.currency_id")
    date = fields.Datetime(string="Generated on", compute="_compute_facts")
    year_progress_percentage = fields.Float(
        compute="_compute_year_progress_percentage", string="Year Progress (%)"
    )

    # Facts
    revenue = fields.Monetary(compute="_compute_facts", currency_field="currency_id")
    cost = fields.Monetary(compute="_compute_facts", currency_field="currency_id")
    profit = fields.Monetary(compute="_compute_facts", currency_field="currency_id")
    taxable_income = fields.Monetary(
        compute="_compute_facts", currency_field="currency_id"
    )
    tax = fields.Monetary(compute="_compute_facts", currency_field="currency_id")
    tax_prepaid = fields.Monetary(
        compute="_compute_facts", currency_field="currency_id", string="Prepaid Tax"
    )
    tax_residual = fields.Monetary(
        compute="_compute_facts",
        currency_field="currency_id",
        string="Tax to Pay (estimation)",
    )

    # Forecast
    forecast_revenue = fields.Monetary(
        compute="_compute_forecast", currency_field="currency_id", string="Revenue"
    )
    forecast_cost = fields.Monetary(
        compute="_compute_forecast", currency_field="currency_id", string="Cost"
    )
    forecast_profit = fields.Monetary(
        compute="_compute_forecast", currency_field="currency_id", string="Profit"
    )
    forecast_taxable_income = fields.Monetary(
        compute="_compute_forecast",
        currency_field="currency_id",
        string="Taxable Income",
    )
    forecast_tax = fields.Monetary(
        compute="_compute_forecast", currency_field="currency_id", string="Tax"
    )
    forecast_tax_prepaid = fields.Monetary(
        compute="_compute_forecast", currency_field="currency_id", string="Prepaid Tax"
    )
    forecast_tax_residual = fields.Monetary(
        compute="_compute_forecast",
        currency_field="currency_id",
        string="Tax to Pay (estimation)",
    )

    # Logs
    factual_log_ids = fields.One2many(
        comodel_name="l10n.nl.income.tax.log",
        inverse_name="report_id",
        domain=[("type", "=", "factual")],
        string="Details",
        compute="_compute_facts",
    )
    forecast_log_ids = fields.One2many(
        comodel_name="l10n.nl.income.tax.log",
        inverse_name="report_id",
        domain=[("type", "=", "forecast")],
        string="Details",
        compute="_compute_forecast",
    )

    # Options
    starters_deduction = fields.Boolean(string="Apply Starter's Deduction")

    def _get_options_fields(self):
        return ["starters_deduction"]

    def name_get(self):
        return [(report.id, report.year_id.year) for report in self]

    @api.onchange("prepaid_tax_account_id")
    def _onchange_prepaid_tax_account_id(self):
        self.env["ir.default"].sudo().set(
            self._name, "prepaid_tax_account_id", self.prepaid_tax_account_id.id
        )

    @api.model
    def _prepare_logs(self, logs):
        return logs

    @api.depends("year_id", "date")
    def _compute_year_progress_percentage(self):
        for report in self:
            now = fields.Datetime.from_string(report.date)
            report.year_progress_percentage = 0
            if report.year_id:
                start = fields.Datetime.from_string(report.year_id.start)
                diff_in_days = (now - start).days / report.year_id.days_in_year
                perc = min(max(diff_in_days, 0), 1)
                report.year_progress_percentage = perc

    def _get_revenue_and_cost(self):
        self.ensure_one()
        year_domain = self.year_id.account_move_line_domain()
        revenue_lines = self.env["account.move.line"].search(
            [
                (
                    "account_id.user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_revenue").id,
                ),
                ("move_id.state", "=", "posted"),
            ]
            + year_domain
        )
        cost_lines = self.env["account.move.line"].search(
            [
                (
                    "account_id.user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_direct_costs").id,
                ),
                ("move_id.state", "=", "posted"),
            ]
            + year_domain
        )
        return {
            "revenue": sum(revenue_lines.mapped("credit")),
            "cost": sum(cost_lines.mapped("debit")),
        }

    @api.depends(
        lambda self: ["year_id", "prepaid_tax_account_id"] + self._get_options_fields()
    )
    def _compute_facts(self):
        for report in self:
            report.revenue = 0
            report.cost = 0
            report.profit = 0
            report.taxable_income = 0
            report.tax = 0
            report.tax_prepaid = 0
            report.tax_residual = 0
            report.factual_log_ids = self.env["l10n.nl.income.tax.log"]
            report.date = False

            if report.year_id:
                report.date = fields.Datetime.now()
                if report.prepaid_tax_account_id:
                    year_domain = self.year_id.account_move_line_domain()
                    report.tax_prepaid = sum(
                        self.env["account.move.line"]
                        .search(
                            [
                                ("account_id", "=", report.prepaid_tax_account_id.id),
                                ("move_id.state", "=", "posted"),
                            ]
                            + year_domain
                        )
                        .mapped("debit")
                    )
                stats = report._get_revenue_and_cost()

                report.revenue = stats["revenue"]
                report.cost = stats["cost"]
                report.profit = report.revenue - report.cost

                taxable_income, tax, logs = report.year_id.apply_rules(
                    report.profit, report
                )
                report.taxable_income = taxable_income
                report.tax = tax
                report.tax_residual = tax - report.tax_prepaid
                logs = self.env["l10n.nl.income.tax.log"].create(
                    self._prepare_logs(logs)
                )
                report.factual_log_ids = logs
                report.date = datetime.now()

    @api.depends(
        "year_id", "revenue", "cost", "year_progress_percentage", "tax_prepaid"
    )
    def _compute_forecast(self):
        for report in self:
            report.forecast_revenue = 0
            report.forecast_cost = 0
            report.forecast_profit = 0
            report.forecast_taxable_income = 0
            report.forecast_tax = 0
            report.forecast_tax_prepaid = 0
            report.forecast_tax_residual = 0
            report.forecast_log_ids = self.env["l10n.nl.income.tax.log"]

            if not report.year_id or not (0 < report.year_progress_percentage < 1):
                continue
            days_gone_by = report.year_id.days_in_year * report.year_progress_percentage
            revenue_per_day = report.revenue / days_gone_by
            cost_per_day = report.cost / days_gone_by
            prepaid_tax_per_day = (
                report.tax_prepaid / days_gone_by
            )  # TODO: This can be more accurate counting the number of lines * months
            report.forecast_revenue = revenue_per_day * report.year_id.days_in_year
            report.forecast_cost = cost_per_day * report.year_id.days_in_year
            report.forecast_profit = report.forecast_revenue - report.forecast_cost
            report.forecast_tax_prepaid = (
                prepaid_tax_per_day * report.year_id.days_in_year
            )

            taxable_income, tax, logs = report.year_id.apply_rules(
                report.forecast_profit, report
            )
            report.forecast_taxable_income = taxable_income
            report.forecast_tax = tax
            report.forecast_tax_residual = tax - report.forecast_tax_prepaid
            logs = self.env["l10n.nl.income.tax.log"].create(self._prepare_logs(logs))
            report.forecast_log_ids = logs

    def action_print(self):
        action = self.env.ref(
            "l10n_nl_income_tax_report.print_income_tax_report_action"
        )
        return action.read()[0]

    def action_drilldown_revenue(self):
        year_domain = self.year_id.account_move_line_domain()
        action = self.env.ref("account.action_account_moves_all").read()[0]
        action["domain"] = [
            (
                "account_id.user_type_id",
                "=",
                self.env.ref("account.data_account_type_revenue").id,
            )
        ] + year_domain
        action["display_name"] = _("Revenue Drilldown")
        return action

    def action_drilldown_cost(self):
        year_domain = self.year_id.account_move_line_domain()
        action = self.env.ref("account.action_account_moves_all").read()[0]
        action["domain"] = [
            (
                "account_id.user_type_id",
                "=",
                self.env.ref("account.data_account_type_direct_costs").id,
            )
        ] + year_domain
        action["display_name"] = _("Cost Drilldown")
        return action
