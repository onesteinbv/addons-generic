from datetime import timedelta
from math import floor

from icalendar.cal import Alarm

from odoo import api, models
from odoo.exceptions import ValidationError


class CalendarAlarm(models.Model):
    _inherit = "calendar.alarm"

    @api.model
    def import_caldav_alarm(self, alarm):
        if alarm["ACTION"] not in ("DISPLAY", "AUDIO"):
            raise ValidationError(
                "Only internal notification alarms should be imported"
            )
        total_seconds = abs(alarm["TRIGGER"].dt.total_seconds())
        total_minutes = int(total_seconds / 60)

        existing_alarms = self.search(
            [
                ("alarm_type", "=", "notification"),
                ("duration_minutes", "=", total_minutes),
            ]
        )
        if not existing_alarms:
            existing_alarms = self.create(self._prepare_caldav_to_odoo(alarm))
            existing_alarms._onchange_duration_interval()
        return existing_alarms

    @api.model
    def _prepare_caldav_to_odoo(self, alarm):
        total_seconds = abs(alarm["TRIGGER"].dt.total_seconds())
        total_others = {
            "minutes": total_seconds / 60,
            "hours": total_seconds / 3600,
            "days": total_seconds / 86400,
        }

        # Duration is an integer in Odoo, so we want the largest unit available as integer
        interval = (
            "days"
            if not total_others["days"] % 1
            else "hours"
            if not total_others["hours"] % 1
            else "minutes"
        )

        return {
            "name": "/",
            "alarm_type": "notification",
            "duration": int(floor(total_others[interval])),
            "interval": interval,
        }

    def to_caldav(self):
        ical_alarms = []
        for alarm in self.filtered(lambda a: a.alarm_type == "notification"):
            ical_alarm = Alarm()
            ical_alarm.add("ACTION", "DISPLAY")
            ical_alarm.add("TRIGGER", timedelta(minutes=alarm.duration_minutes))
            ical_alarms.append(ical_alarm)
        return ical_alarms
