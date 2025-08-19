from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def calculate_recurring_next_date(self, start_date):
        if self.account_invoice_ids_count == 0:
            self.recurring_next_date = date.today()
        else:
            if self.sale_subscription_line_ids.mapped("product_id").filtered(
                lambda x: x.first_of_period_billing_policy
                and x.membership_type == "variable"
            ):
                type_interval = self.template_id.recurring_rule_type
                interval = int(self.template_id.recurring_interval)
                next_date = start_date + relativedelta(**{type_interval: interval})
                if type_interval == "weeks":
                    # New next_date is on a Monday
                    if next_date.weekday() != 0:
                        next_date = next_date + relativedelta(
                            days=7 - next_date.weekday()
                        )
                elif type_interval == "months":
                    # New next_date is 1st of month
                    next_date = next_date.replace(day=1)
                elif type_interval == "years":
                    # New next_date is 1st of January
                    next_date = next_date.replace(day=1, month=1)
                self.recurring_next_date = next_date
            else:
                return super(SaleSubscription, self).calculate_recurring_next_date(
                    start_date
                )
