from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def get_next_interval(self, type_interval, interval):
        self.ensure_one()
        subscriptions = self.subscription_ids.filtered(
            lambda x: x.template_id.recurring_rule_type == type_interval
            and x.template_id.recurring_interval == interval
        )
        if subscriptions:
            subscription = subscriptions[0]
            if subscription.sale_subscription_line_ids.mapped("product_id").filtered(
                lambda x: x.first_of_period_billing_policy
                and x.membership_type == "variable"
            ):
                start_date = date.today()
                type_interval = subscription.template_id.recurring_rule_type
                interval = int(subscription.template_id.recurring_interval)
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

                return next_date
        return super(SaleOrder, self).get_next_interval(type_interval, interval)
