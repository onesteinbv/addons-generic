from collections import namedtuple
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from odoo.addons.resource.models.resource import float_to_time

DummyAttendance = namedtuple(
    "DummyAttendance", "hour_from, hour_to, dayofweek, day_period, week_type"
)


def find_all_dates_for_day_of_week_between_range(start, end, weekday):
    total_days = (end - start).days
    all_days = [start + timedelta(days=day) for day in range(total_days)]
    return [day for day in all_days if day.weekday() == int(weekday)]


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    @api.model
    def _update_contract_time_off(self):  # noqa: disable=C901
        """
        Method called by the cron task in order to update the contract
        time off for resources.
        """
        today = fields.Datetime.today()
        three_months_from_today = today + relativedelta(months=3)
        resource_calendars = self.search([("two_weeks_calendar", "=", False)])
        resource_obj = self.env["resource.resource"]
        hr_leave_obj = self.env["hr.leave"]
        contract_time_off_holiday_status_id = self.env.ref(
            "hr_holidays_resource.holiday_status_cto", raise_if_not_found=False
        )
        contract_time_off_partial_holiday_status_id = self.env.ref(
            "hr_holidays_resource.holiday_status_ctop", raise_if_not_found=False
        )
        for resource_calendar in resource_calendars:
            non_working_periods = {}
            for day in ["0", "1", "2", "3", "4"]:
                working_periods = resource_calendar.attendance_ids.filtered(
                    lambda r: r.dayofweek == day
                )
                if not working_periods:
                    non_working_periods.update({day: "full day"})
                    continue
                if not working_periods.filtered(lambda wp: wp.day_period == "morning"):
                    non_working_periods.update({day: "morning"})
                    continue
                if not working_periods.filtered(
                    lambda wp: wp.day_period == "afternoon"
                ):
                    non_working_periods.update({day: "afternoon"})
                    continue
            if non_working_periods:
                attendances = self._get_attendances(resource_calendar.id)
                for day, period in non_working_periods.items():
                    all_non_working_dates = (
                        find_all_dates_for_day_of_week_between_range(
                            today, three_months_from_today, day
                        )
                    )
                    if period == "full day":
                        if contract_time_off_holiday_status_id:
                            for resource in resource_obj.search(
                                [
                                    ("calendar_id", "=", resource_calendar.id),
                                    ("resource_type", "=", "user"),
                                ]
                            ):
                                for non_working_date in all_non_working_dates:
                                    try:
                                        with self.env.cr.savepoint():
                                            hr_leave_obj.create(
                                                self.prepare_hr_leave_vals(
                                                    non_working_date,
                                                    contract_time_off_holiday_status_id,
                                                    resource,
                                                    attendances,
                                                )
                                            )
                                    except Exception:
                                        continue
                    else:
                        if contract_time_off_partial_holiday_status_id:
                            for resource in resource_obj.search(
                                [
                                    ("calendar_id", "=", resource_calendar.id),
                                    ("resource_type", "=", "user"),
                                ]
                            ):
                                for non_working_date in all_non_working_dates:
                                    try:
                                        with self.env.cr.savepoint():
                                            hr_leave_obj.create(
                                                self.prepare_hr_leave_vals(
                                                    non_working_date,
                                                    contract_time_off_holiday_status_id,
                                                    resource,
                                                    attendances,
                                                    period,
                                                )
                                            )
                                    except Exception:
                                        continue

    def prepare_hr_leave_vals(
        self, date, holiday_status_id, resource, attendances, period=False
    ):
        employee = resource.employee_id[0]
        vals = {
            "holiday_status_id": holiday_status_id.id,
            "employee_id": employee.id,
            "number_of_days": 1,
        }
        default_value = DummyAttendance(0, 0, 0, "morning", False)
        if period:
            # find first attendance coming after first_day for the specified period
            attendance_from = next(
                (att for att in attendances if att.day_period == period),
                attendances[0] if attendances else default_value,
            )
            # find last attendance coming before last_day for the specified period
            attendance_to = next(
                (att for att in reversed(attendances) if att.day_period == period),
                attendances[-1] if attendances else default_value,
            )
        else:
            # find first attendance coming after first_day
            attendance_from = next(
                (att for att in attendances if int(att.dayofweek) >= date.weekday()),
                attendances[0] if attendances else default_value,
            )
            # find last attendance coming before last_day
            attendance_to = next(
                (
                    att
                    for att in reversed(attendances)
                    if int(att.dayofweek) <= date.weekday()
                ),
                attendances[-1] if attendances else default_value,
            )
        hour_from = float_to_time(attendance_from.hour_from)
        hour_to = float_to_time(attendance_to.hour_to)
        hour_from = hour_from.hour + hour_from.minute / 60
        hour_to = hour_to.hour + hour_to.minute / 60

        vals["date_from"] = self.env["hr.leave"]._get_start_or_end_from_attendance(
            hour_from, date.date(), employee
        )
        vals["date_to"] = self.env["hr.leave"]._get_start_or_end_from_attendance(
            hour_to, date.date(), employee
        )
        vals["request_date_from"], vals["request_date_to"] = (
            vals["date_from"].date(),
            vals["date_to"].date(),
        )
        if period:
            vals.update(
                {
                    "number_of_days": 0.5,
                    "request_date_from_period": "am" if period == "morning" else "pm",
                    "request_unit_half": True,
                    "request_date_from": vals["date_from"],
                    "request_date_to": vals["date_to"],
                }
            )
        else:
            vals.update({"number_of_days": 1})
        return vals

    def _get_attendances(self, resource_calendar_id):
        domain = [
            ("calendar_id", "=", resource_calendar_id),
            ("display_type", "=", False),
        ]
        attendances = self.env["resource.calendar.attendance"].read_group(
            domain,
            [
                "ids:array_agg(id)",
                "hour_from:min(hour_from)",
                "hour_to:max(hour_to)",
                "week_type",
                "dayofweek",
                "day_period",
            ],
            ["week_type", "dayofweek", "day_period"],
            lazy=False,
        )

        # Must be sorted by dayofweek ASC and day_period DESC
        attendances = sorted(
            [
                DummyAttendance(
                    group["hour_from"],
                    group["hour_to"],
                    group["dayofweek"],
                    group["day_period"],
                    group["week_type"],
                )
                for group in attendances
            ],
            key=lambda att: (att.dayofweek, att.day_period != "morning"),
        )
        return attendances
