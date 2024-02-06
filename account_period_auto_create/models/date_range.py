# Copyright 2017-2018 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from dateutil.rrule import MONTHLY

from odoo import api, fields, models


class DateRange(models.Model):
    _inherit = "date.range"

    @api.model
    def cron_create_fiscal_periods(self):
        # Monthly and quarterly for next year
        for company in self.env["res.company"].search([]):
            for i in range(-1, 4):
                nextyear_str = "%s" % (datetime.now().year + i)
                nextyear_start = fields.Date.from_string(nextyear_str + "-01-01")
                fiscal_periods = self.search(
                    [
                        ("company_id", "=", company.id),
                        ("date_start", ">=", nextyear_start),
                        "|",
                        ("type_id.fiscal_period_month", "=", True),
                        ("type_id.fiscal_period_quarter", "=", True),
                    ]
                )
                if not fiscal_periods:
                    fiscalperiodmonth = self.env.ref(
                        "account_period_auto_create.fiscalperiodmonth"
                    )
                    period_company = fiscalperiodmonth.company_id
                    if not period_company or period_company == company:
                        wizard = self.env["date.range.generator"].create(
                            {
                                "name_prefix": "M " + nextyear_str + " ",
                                "date_start": nextyear_start,
                                "type_id": fiscalperiodmonth.id,
                                "company_id": company.id,
                                "unit_of_time": str(MONTHLY),
                                "duration_count": 1,
                                "count": 12,
                            }
                        )
                        wizard.action_apply()
                    fiscalperiodquarter = self.env.ref(
                        "account_period_auto_create.fiscalperiodquarter"
                    )
                    period_company = fiscalperiodquarter.company_id
                    if not period_company or period_company == company:
                        wizard = self.env["date.range.generator"].create(
                            {
                                "name_prefix": "Q " + nextyear_str + " ",
                                "date_start": nextyear_start,
                                "type_id": fiscalperiodquarter.id,
                                "company_id": company.id,
                                "unit_of_time": str(MONTHLY),
                                "duration_count": 3,
                                "count": 4,
                            }
                        )
                        wizard.action_apply()

            # Fiscal years
            for i in range(-1, 4):
                nextyear_str = "%s" % (datetime.now().year + i)
                nextyear_start = fields.Date.from_string(nextyear_str + "-01-01")
                nextyear_end = fields.Date.from_string(nextyear_str + "-12-31")
                fiscalperiodyear = self.env.ref(
                    "account_period_auto_create.fiscalperiodyear"
                )
                period_company = fiscalperiodyear.company_id
                if not period_company or period_company == company:
                    existing = self.env["date.range"].search(
                        [
                            ("company_id", "=", company.id),
                            ("date_start", "=", nextyear_start),
                            ("date_end", "=", nextyear_end),
                            ("type_id", "=", fiscalperiodyear.id),
                        ],
                        limit=1,
                    )
                    if not existing:
                        self.env["date.range"].create(
                            {
                                "name": "Y " + nextyear_str,
                                "date_start": nextyear_start,
                                "date_end": nextyear_end,
                                "type_id": fiscalperiodyear.id,
                                "company_id": company.id,
                            }
                        )
