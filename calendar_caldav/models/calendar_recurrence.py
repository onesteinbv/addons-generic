from datetime import datetime, timezone

from dateutil import rrule
from dateutil.rrule import rruleset
from icalendar import vRecur

from odoo import api, fields, models

FIELD_TO_CALDAV_BYDAY_MAP = {
    "mon": "MO",
    "tue": "TU",
    "wed": "WE",
    "thu": "TH",
    "fri": "FR",
    "sat": "SA",
    "sun": "SU",
}


class CalendarRecurrence(models.Model):
    _inherit = "calendar.recurrence"

    byday = fields.Selection(selection_add=[("-2", "Second to last"), ("5", "Fifth")])
    exceptions = fields.Serialized(help="Store exception datetimes")

    def _select_new_base_event(self):
        res = super()._select_new_base_event()
        # If exception dates are before the base_event_id.start we should discount them
        for recurrence in self.filtered(
            lambda r: r.exceptions
            and r.exceptions.get("dts")
            and r.end_type == "count"
            and r.base_event_id
        ):
            # TODO: This is not the way as base event deletion can move the base event more than 1 count
            recurrence.count -= 1
            # TODO: This is the way but I commented it out just to test something else
            # dts = recurrence.exceptions.get("dts", [])
            # occurrences = recurrence._get_occurrences(recurrence.base_event_id.start)
            # occurrences = [o for o in occurrences]
            # out_of_range_events = []
            # for dt in dts:
            #     if recurrence.base_event_id.start >= fields.Datetime.to_datetime(dt):
            #         out_of_range_events.append(dt)
            # for dt in out_of_range_events:
            #     dts.remove(dt)
            # recurrence.exceptions = {
            #     "dts": dts
            # }
            # count = len(occurrences) - len(out_of_range_events)
            # if not self.env.context.get("no_caldav"):
            #     count += 1  # + 1 for the unlinked base_event_id
            # recurrence.count = count
        return res

    def _apply_recurrence(
        self,
        specific_values_creation=None,
        no_send_edit=False,
        generic_values_creation=None,
    ):
        for recurrence in self.filtered(
            lambda r: r.base_event_id and r.end_type == "count" and r.exceptions
        ):
            dts = recurrence.exceptions.get("dts", [])
            out_of_range = []
            for dt in dts:
                exdate = fields.Datetime.to_datetime(dt)
                if exdate < recurrence.base_event_id.start:
                    out_of_range.append(dt)
            for dt in out_of_range:
                dts.remove(dt)
            rrule_set = recurrence._get_rrule(recurrence.base_event_id.start)
            occurrences = [o for o in rrule_set]
            recurrence.exceptions = {"dts": dts}
            new_count = len(occurrences) + len(dts)
            # Caldav / ical can have a recurrent event with count = 1 (so only 1 event is created), but it can have unlimited nonsense exdates
            # There's no validation on it
            if new_count > 0:
                recurrence.count = new_count
            recurrence.base_event_id.start = occurrences[0]

        return super()._apply_recurrence(
            specific_values_creation, no_send_edit, generic_values_creation
        )

    @api.depends("exceptions", "base_event_id", "base_event_id.allday")
    def _compute_rrule(self):
        return super()._compute_rrule()

    def _get_rrule(self, dtstart=None):
        rrule = super()._get_rrule(dtstart)
        # Until date is a fields.Date and Odoo will set _until to calendar.recurrence.until + time.max
        # which will result in discrepancies between odoo / caldav
        if (
            self.end_type == "end_date"
            and self.base_event_id
            and not self.base_event_id.allday
        ):
            rrule._until = datetime.combine(
                rrule._until.date(), self.base_event_id.start.time()
            )

        # dtstart is a timezoned datetime (without tzinfo) (so are the occurrences)
        if not self.exceptions or not self.exceptions.get("dts"):
            return rrule
        rrule_set = rruleset()
        rrule_set.rrule(rrule)
        tz = self._get_timezone()
        for exception in self.exceptions["dts"]:
            as_utc = fields.Datetime.to_datetime(exception)
            with_timezone = as_utc.astimezone(tz)  # Midnight cases
            if dtstart:
                with_timezone = datetime.combine(with_timezone.date(), dtstart.time())
            rrule_set.exdate(with_timezone.replace(tzinfo=None))  # Timezoned
        return rrule_set

    def _rrule_serialize(self):
        rrule = self._get_rrule()
        if type(rrule) is rruleset:
            tz = self._get_timezone()
            exdate_strs = []
            for exdate in rrule._exdate:
                exdate_strs.append(
                    "EXDATE;TZID=%s:%s" % (tz, exdate.strftime("%Y%m%dT%H%M%S"))
                )
            return "\n".join(exdate_strs + [str(rrule._rrule[0])])
        return super()._rrule_serialize()

    def add_exception(self, dt):
        self.ensure_one()
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc)
            dt = dt.replace(tzinfo=None)
        dts = self.exceptions.get("dts", [])
        dts.append(fields.Datetime.to_string(dt))
        self.exceptions = {"dts": dts}

    @api.model
    def _rrule_parse(self, rule_str, date_start):
        values = super()._rrule_parse(
            "\n".join(
                filter(lambda line: not line.startswith("EXDATE"), rule_str.split("\n"))
            ),
            date_start,
        )
        rule = rrule.rrulestr(rule_str, dtstart=date_start, forceset=True)
        exceptions = []
        for exdate in rule._exdate:
            as_utc = exdate.astimezone(timezone.utc)
            exceptions.append(fields.Datetime.to_string(as_utc.replace(tzinfo=None)))
        values["exceptions"] = {"dts": exceptions}
        return values

    def _range_calculation(self, event, duration):
        self.ensure_one()
        original_count = self.count
        if self.exceptions and self.end_type == "count":
            self.count -= len(
                self.exceptions["dts"]
            )  # Odoo will always try to make equal to count, but we don't want that with exceptions
        res = super()._range_calculation(event, duration)
        self.count = original_count
        return res

    def to_caldav(self):
        self.ensure_one()
        rrule_lines = list(
            map(
                lambda line: line.replace("RRULE:", ""),
                filter(lambda line: line.startswith("RRULE"), self.rrule.splitlines()),
            )
        )
        recur = vRecur.from_ical("\n".join(rrule_lines))
        return recur
