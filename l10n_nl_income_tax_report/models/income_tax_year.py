import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class IncomeTaxYear(models.Model):
    _name = "l10n.nl.income.tax.year"
    _description = "Tax Year"
    _order = "year desc"

    currency_id = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.ref("base.EUR").id
    )
    year = fields.Integer(required=True)
    start = fields.Datetime(compute="_compute_year_dates")
    end = fields.Datetime(compute="_compute_year_dates")
    days_in_year = fields.Integer()
    rule_ids = fields.One2many(
        comodel_name="l10n.nl.income.tax.rule", inverse_name="year_id"
    )

    _sql_constraints = [("year_uniq", "unique(year)", "Year already exists.")]

    @api.depends("year")
    def _compute_name(self):
        for record in self:
            record.name = record.year and str(record.year)

    @api.depends("year")
    def _compute_year_dates(self):
        for record in self:
            start = datetime.datetime(record.year, 1, 1)
            end = datetime.datetime(record.year + 1, 1, 1)
            record.start = start
            record.end = end
            record.days_in_year = (end - start).days

    def account_move_line_domain(self, year=None):
        record = self
        if isinstance(year, int):
            record = self.search([("year", "=", year)])
            if not record:
                raise UserError(_("Year configuration for %s not found") % year)
        elif year is not None:
            record = year

        start = fields.Datetime.from_string(record.start)
        end = fields.Datetime.from_string(record.end)

        return [("date", ">=", start.date()), ("date", "<", end.date())]

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, str(record.year)))
        return res

    def apply_rules(self, taxable_income, report):
        return self.rule_ids.apply(taxable_income, report)
