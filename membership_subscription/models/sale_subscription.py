from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def calculate_recurring_next_date(self, start_date):
        lines = self.sale_subscription_line_ids
        if self.account_invoice_ids_count == 0 and not lines.product_id.filtered(
            lambda x: x.membership_skip_invoice
        ):
            self.recurring_next_date = date.today()
        else:
            if lines.product_id.filtered(
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

    def _generate_subscription_date_range(self):
        self.ensure_one()
        if self._membership_skip_invoice():
            start_date = self.recurring_next_date or self.date_start
            end_date = self._calculate_recurring_next_date(start_date)
            return start_date, end_date
        return super()._generate_subscription_date_range()

    def generate_invoice(self):
        if self._membership_skip_invoice():
            self._membership_generate_membership_lines()
            return
        return super(SaleSubscription, self).generate_invoice()

    def create_invoice(self):
        if self._membership_skip_invoice():
            self._membership_generate_membership_lines()
            return
        return super(SaleSubscription, self).create_invoice()

    def manual_invoice(self):
        if self._membership_skip_invoice():
            self._membership_generate_membership_lines()
            return

    def _membership_skip_invoice(self):
        return bool(
            self.sale_subscription_line_ids.filtered(
                lambda x: x.product_id.membership
                and x.product_id.membership_skip_invoice
            )
        )

    def _membership_generate_membership_lines(self):
        memberships_vals = []
        for line in self.sale_subscription_line_ids.filtered(
            lambda x: x.product_id.membership and x.product_id.membership_skip_invoice
        ):
            subscription = line.sale_subscription_id
            date_from, date_to = subscription._generate_subscription_date_range()
            memberships_vals.append(
                {
                    "partner": subscription.partner_id.id,
                    "membership_id": line.product_id.id,
                    "member_price": line.price_unit,
                    "date": fields.Date.today(),
                    "date_from": date_from,
                    "date_to": date_to,
                    "state": "free",
                }
            )
            subscription.calculate_recurring_next_date(subscription.recurring_next_date)

        self.env["membership.membership_line"].create(memberships_vals)
