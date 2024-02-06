# Copyright 2017-2018 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_period_month = fields.Boolean(string="Is fiscal month?")
    fiscal_period_quarter = fields.Boolean(string="Is fiscal quarter?")
    fiscal_period_year = fields.Boolean(string="Is fiscal year?")

    @api.ondelete(at_uninstall=False)
    def _unlink_except_fiscal_period(self):
        for rec in self:
            if (
                rec.fiscal_period_month
                or rec.fiscal_period_quarter
                or rec.fiscal_period_year
            ):
                if rec.date_range_ids:
                    raise exceptions.ValidationError(
                        _(
                            "You cannot delete a date range type with flag "
                            '"fiscal_period_month" or "fiscal_period_quarter" or "fiscal_period_year"'
                        )
                    )
