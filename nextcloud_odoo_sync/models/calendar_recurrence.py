# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields, _
from dateutil import rrule
from odoo.exceptions import UserError
from datetime import timedelta,datetime

SELECT_FREQ_TO_RRULE = {
    'daily': rrule.DAILY,
    'weekly': rrule.WEEKLY,
    'monthly': rrule.MONTHLY,
    'yearly': rrule.YEARLY,
}

RRULE_WEEKDAYS = {'SUN': 'SU', 'MON': 'MO', 'TUE': 'TU', 'WED': 'WE', 'THU': 'TH', 'FRI': 'FR', 'SAT': 'SA'}


def freq_to_rrule(freq):
    return SELECT_FREQ_TO_RRULE[freq]

def weeks_between(start_date, end_date):
    weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_date)
    return weeks.count() - 1

def months_between(start_date, end_date):
    months = rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date)
    return months.count() - 1

def years_between(start_date, end_date):
    years = rrule.rrule(rrule.YEARLY, dtstart=start_date, until=end_date)
    return years.count() - 1

def days_between(start_date, end_date):
    days = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)
    return days.count() - 1


class CalendarRecurrence(models.Model):
    _inherit = "calendar.recurrence"

    nc_exdate = fields.Char("Nextcloud Exdate")



    def _get_rrule(self, dtstart=None):
        self.ensure_one()

        if self._context.get('update_until', False):
            if self.until:
                self.until = self.until - timedelta(days=1)
        if not self.base_event_id.nc_calendar_id or self.end_type != 'forever':
            return super()._get_rrule(dtstart)
        freq = self.rrule_type
        rrule_params = dict(
            dtstart=dtstart,
            interval=self.interval,
        )
        today = datetime.today().date()
        dtstart_date = (self.dtstart or dtstart).date()
        past_event = True if (today - dtstart_date).days > 0 else False
        config = self.env["ir.config_parameter"].sudo()
        if freq == 'monthly' and self.month_by == 'date':  # e.g. every 15th of the month
            rrule_params['bymonthday'] = self.day
        elif freq == 'monthly' and self.month_by == 'day':  # e.g. every 2nd Monday in the month
            rrule_params['byweekday'] = getattr(rrule, RRULE_WEEKDAYS[self.weekday])(
                int(self.byday))  # e.g. MO(+2) for the second Monday of the month
        elif freq == 'weekly':
            weekdays = self._get_week_days()
            if not weekdays:
                raise UserError(_("You have to choose at least one day in the week"))
            rrule_params['byweekday'] = weekdays
            rrule_params['wkst'] = self._get_lang_week_start()
            weekly_recurring_events_limit_value = (2
                                                   if not config.get_param(
                "nextcloud_odoo_sync.weekly_recurring_events_limit")
                                                   else int(config.get_param(
                "nextcloud_odoo_sync.weekly_recurring_events_limit"))
                                                   ) * 52
            if past_event:
                weekly_recurring_events_limit_value += weeks_between(dtstart_date,today)
            rrule_params['count'] = ((
                                             weekly_recurring_events_limit_value // self.interval) if self.interval < weekly_recurring_events_limit_value else 1) * len(
                weekdays)  # maximum recurring events for 2 years

        elif freq == 'daily':
            daily_recurring_events_limit_value = (2
                                                  if not config.get_param(
                "nextcloud_odoo_sync.daily_recurring_events_limit")
                                                  else int(config.get_param(
                "nextcloud_odoo_sync.daily_recurring_events_limit")
                                                  )) * 365
            if past_event:
                daily_recurring_events_limit_value += days_between(dtstart_date,today)
            rrule_params['count'] = (
                    daily_recurring_events_limit_value // self.interval) if self.interval < daily_recurring_events_limit_value else 1  # maximum recurring events for 2 years
        if freq in ('yearly', 'monthly'):
            yearly_recurring_events_limit_value = (10
                                                   if not config.get_param(
                "nextcloud_odoo_sync.yearly_recurring_events_limit")
                                                   else int(config.get_param(
                "nextcloud_odoo_sync.yearly_recurring_events_limit")
                                                   ))
            monthly_recurring_events_limit_value = (2
                                                    if not config.get_param(
                "nextcloud_odoo_sync.monthly_recurring_events_limit")
                                                    else int(config.get_param(
                "nextcloud_odoo_sync.monthly_recurring_events_limit")
                                                    )) * 12
            if freq == 'yearly':
                if past_event:
                    yearly_recurring_events_limit_value += years_between(dtstart_date, today)
                rrule_params['count'] = (
                        yearly_recurring_events_limit_value // self.interval) if self.interval < yearly_recurring_events_limit_value else 1  # maximum recurring events for 10 years
            elif freq == 'monthly':
                if self.interval >= 12:
                    if past_event:
                        yearly_recurring_events_limit_value += years_between(dtstart_date, today)
                    rrule_params['count'] = (yearly_recurring_events_limit_value // (
                            self.interval // 12))  # maximum recurring events for years defined
                else:
                    if past_event:
                        monthly_recurring_events_limit_value += months_between(dtstart_date, today)
                    rrule_params['count'] = (
                            monthly_recurring_events_limit_value // self.interval)  # maximum recurring events for months defined

        return rrule.rrule(
            freq_to_rrule(freq), **rrule_params
        )
