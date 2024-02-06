import re
from datetime import date, datetime, timedelta, timezone

from caldav import Event as CalDAVEvent
from caldav.elements import cdav
from caldav.lib.error import NotFoundError
from icalendar.cal import Alarm, Event
from icalendar.prop import vDDDTypes

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.calendar.models.calendar_recurrence import weekday_to_field

CALDAV_BYDAY_TO_FIELD_MAP = {  # TODO: move to calendar_recurrence.py
    "MO": "mon",
    "TU": "tue",
    "WE": "wed",
    "TH": "thu",
    "FR": "fri",
    "SA": "sat",
    "SU": "sun",
}

CALDAV_BYDAY_TO_SEQUENCE = {  # TODO: move to calendar_recurrence.py
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    caldav_url = fields.Char()
    caldav_dtstamp = fields.Datetime()
    caldav_organizer = fields.Char()
    caldav_calendar_id = fields.Many2one(
        comodel_name="calendar.caldav",
        string="CalDAV Calendar",
        default=lambda self: self.env.user.default_caldav_calendar_id.id,
        ondelete="cascade",
    )
    byday = fields.Selection(selection_add=[("-2", "Second to last"), ("5", "Fifth")])
    exceptions = fields.Serialized(compute="_compute_recurrence", readonly=False)

    @api.model
    def _get_recurrent_fields(self):
        fields = super()._get_recurrent_fields()
        fields.add("exceptions")
        return fields

    @api.model
    def _caldav_datetime_to_odoo(self, dt):
        is_date = type(dt) is date
        if not is_date:
            dt = dt.astimezone(timezone.utc)
            dt = dt.replace(tzinfo=None)
        return dt

    # TODO: Move to caldav.calendar?
    @api.model
    def _fetch_caldav_events(self, caldav_calendar, date_from=None):
        calendar = caldav_calendar.get_caldav_object()

        filters = []
        if date_from:
            filters.append(cdav.PropFilter("DTSTAMP") + cdav.TimeRange(start=date_from))
        caldav_events = calendar.search(
            comp_class=CalDAVEvent, event=True, expand=False, filters=filters
        )
        return caldav_events

    @api.model
    def cleanup_caldav_events(self, caldav_calendar):
        # Try to be as light as possible
        caldav_object = caldav_calendar.get_caldav_object()
        self.env.cr.execute(
            "SELECT DISTINCT caldav_url FROM calendar_event WHERE caldav_calendar_id = %s AND caldav_url IS NOT NULL",
            (caldav_calendar.id,),
        )
        # Do we care if a past event is deleted?
        to_check = self.env.cr.fetchall()
        for item in to_check:
            canonical_url = item[0]
            response = caldav_object.client.request(canonical_url)
            if response.status == 404:
                # Check on caldav_calendar_id is not really necessary
                self.env.cr.execute(
                    "DELETE FROM calendar_event WHERE caldav_calendar_id = %s AND caldav_url = %s",
                    (caldav_calendar.id, canonical_url),
                )

    # TODO: Move to caldav.calendar?
    @api.model
    def import_caldav_events(self, caldav_calendar, date_from=None):
        caldav_events = self._fetch_caldav_events(caldav_calendar, date_from=date_from)

        for caldav_event in caldav_events:
            ical = caldav_event.icalendar_component
            url = caldav_event.canonical_url
            event = self.search(
                [
                    ("caldav_url", "=", url),
                    ("caldav_calendar_id", "=", caldav_calendar.id),
                ]
            )
            values = {
                "caldav_url": caldav_event.canonical_url,
            }
            values.update(self._caldav_vevent_to_odoo(ical, caldav_calendar))

            # Recurring rule
            if ical.get("RRULE"):
                values.update(self._caldav_vrecur_to_odoo(ical.get("RRULE"), ical))
                event = event.filtered(lambda e: e.recurrence_id.base_event_id == e)
            else:
                values["recurrency"] = False

            # Alarms
            alarms = list(filter(lambda s: type(s) is Alarm, ical.subcomponents))
            values.update(self._caldav_valarm_to_odoo(alarms))

            if event:
                attendee_ids = values.pop("attendee_ids")
                attendee_values = {
                    "attendee_ids": attendee_ids,
                }
                if values["recurrency"]:
                    values["recurrence_update"] = "all_events"
                    attendee_values["recurrence_update"] = "all_events"

                # Add context to prevent recursion
                event_with_no_caldav = event.with_context(no_caldav=True)
                # partner_ids will set attendee_ids in write method, so we need to do this 2 times
                event_with_no_caldav.write(values)
                # If event is archived / detached by the previous write, ignore it
                if event_with_no_caldav.active:
                    event_with_no_caldav.write(attendee_values)
            else:
                event = self.with_context(no_caldav=True).create(values)

            # Attachments (we need the event id for this so no multi_create)
            attachments = self.env["ir.attachment"]
            if ical.get("ATTACH"):
                attachments = self.env["ir.attachment"].import_caldav_attachments(
                    ical.get("ATTACH"), event
                )
            self.env["ir.attachment"].search(
                [
                    ("type", "=", "url"),
                    ("res_model", "=", "calendar.event"),
                    ("res_id", "=", event.id),
                    ("id", "not in", attachments.ids),
                ]
            ).unlink()

    @api.model
    def _caldav_valarm_to_odoo(self, valarms):
        calendar_alarms = self.env["calendar.alarm"]
        for alarm in valarms:
            if (
                alarm["TRIGGER"].params.get("VALUE") == "DATE-TIME"
            ):  # Alarms not related to the start date
                continue  # Not sure what to do with these cases, make module to implement this?
            if alarm["ACTION"] not in (
                "DISPLAY",
                "AUDIO",
            ):  # Only alarms which show in-system notification as others use email or sms
                continue
            calendar_alarms += self.env["calendar.alarm"].import_caldav_alarm(alarm)

        # First remove all internal alarm and then relink them to not remove email / sms alarms
        notification_alarms = self.env["calendar.alarm"].search(
            [("alarm_type", "=", "notification")]
        )
        return {
            "alarm_ids": [
                Command.unlink(alarm_id) for alarm_id in notification_alarms.ids
            ]
            + [Command.link(alarm_id) for alarm_id in calendar_alarms.ids]
        }

    @api.model
    def _caldav_vrecur_to_odoo(
        self, vrecur, vevent
    ):  # TODO: Move to calendar.recurrence
        # I'm not sure why this is a list
        # Odoo doesn't support secondly, minutely, hourly just let it be as I can't find any calendar that does
        values = {
            "recurrency": True,
            "rrule_type": vrecur["FREQ"][0].lower(),
            "end_type": "forever",
        }

        if vrecur.get("INTERVAL"):
            values.update({"interval": vrecur["INTERVAL"][0]})

        if vrecur.get("UNTIL"):
            until = self._caldav_datetime_to_odoo(vrecur["UNTIL"][0])
            values.update(
                {
                    "until": type(until) is date and until or until.date(),
                    "end_type": "end_date",
                }
            )

        if values["rrule_type"] == "weekly":
            if vrecur.get("BYDAY"):
                for weekday in vrecur["BYDAY"]:
                    values.update({CALDAV_BYDAY_TO_FIELD_MAP[weekday]: True})
            else:
                weekday_field_name = weekday_to_field(vevent["DTSTART"].dt.weekday())
                values.update({weekday_field_name: True})

        if vrecur.get("COUNT"):
            values.update({"end_type": "count", "count": vrecur["COUNT"][0]})

        if vrecur.get("BYSETPOS"):
            values.update({"byday": str(vrecur["BYSETPOS"][0])})

        if vrecur.get("BYMONTHDAY"):
            values.update(
                {
                    "month_by": "dates",
                    "day_ids": [
                        Command.set(
                            [
                                self.env["calendar.recurrence.day"].get_id_from_day(d)
                                for d in vrecur["BYMONTHDAY"]
                            ]
                        )
                    ],
                }
            )

        if vrecur.get("BYDAY") and values["rrule_type"] == "monthly":
            byday = vrecur.get("BYDAY")
            weekday_ids = []
            if len(byday) == 1:
                weekday = CALDAV_BYDAY_TO_FIELD_MAP[byday[0]].upper()
            elif len(byday) == 7:
                weekday = "day"
            else:
                weekday_ids = [
                    self.env["calendar.recurrence.weekday"].get_id_by_sequence(
                        CALDAV_BYDAY_TO_SEQUENCE[d]
                    )
                    for d in byday
                ]
                weekday_ids_set = set(weekday_ids)
                weekend_days_ids = set(
                    self.env["calendar.recurrence.weekday"].get_ids_of_weekend_days()
                )
                week_days_ids = set(
                    self.env["calendar.recurrence.weekday"].get_ids_of_weekdays()
                )
                if weekday_ids_set == weekend_days_ids:
                    weekday = "weekend_day"
                elif weekday_ids_set == week_days_ids:
                    weekday = "weekday"
                else:
                    weekday = "custom"

            values.update(
                {
                    "month_by": "day",
                    "weekday": weekday,
                    # Do not include when empty? or will_compute_weekday_ids will overwrite it
                    # anyway if weekday in (weekend_day, day, weekday)?
                    "weekday_ids": [Command.set(weekday_ids)],
                }
            )

        if vevent.get("EXDATE"):
            start = self._caldav_datetime_to_odoo(vevent["DTSTART"].dt)
            is_all_day = type(start) is date
            is_all_day and datetime(start.year, start.month, start.day, 8) or start
            r_exdate_values = []
            exdates = vevent.get("EXDATE")
            exdates = (
                type(exdates) == list and exdates or [exdates]
            )  # Will be not a list if there's just on exdate
            for exdate in exdates:
                exdate = exdate.dts[0].dt  # Weird but it is what it is
                if type(exdate) == date:
                    exdate = datetime(exdate.year, exdate.month, exdate.day)
                    exdate = exdate.replace(
                        hour=8
                    )  # Odoo does this in the inverse method (_inverse_dates) for allday events
                exdate = self._caldav_datetime_to_odoo(exdate)
                r_exdate_values.append(fields.Datetime.to_string(exdate))
            values["exceptions"] = {"dts": r_exdate_values}

        return values

    @api.model
    def _caldav_vevent_to_odoo(self, vevent, caldav_calendar):
        start = self._caldav_datetime_to_odoo(vevent["DTSTART"].dt)
        stop = self._caldav_datetime_to_odoo(vevent["DTEND"].dt)
        allday = type(start) is date
        start_field = allday and "start_date" or "start"
        stop_field = allday and "stop_date" or "stop"
        if allday:
            stop -= timedelta(days=1)

        values = {
            "name": vevent.get("SUMMARY", "/"),
            "allday": allday,
            "description": vevent.get("DESCRIPTION"),
            "location": vevent.get("LOCATION"),
            start_field: start,
            stop_field: stop,
            "show_as": vevent.get("TRANSP") == "TRANSPARENT" and "free" or "busy",
            "caldav_dtstamp": self._caldav_datetime_to_odoo(vevent.get("DTSTAMP").dt),
            "caldav_calendar_id": caldav_calendar.id,
            "mon": False,
            "tue": False,
            "wed": False,
            "thu": False,
            "fri": False,
            "sat": False,
            "sun": False,
        }

        # Attendees
        partner_ids = []
        user = caldav_calendar.user_id
        if vevent.get("ORGANIZER"):
            organizer_match = re.search("^(mailto|MAILTO):(.*)$", vevent["ORGANIZER"])
            if not organizer_match:
                raise Exception(
                    "Regex for ORGANIZER property failed to find an email address (%s)"
                    % vevent["ORGANIZER"]
                )
            organizer_email = organizer_match.group(2)
            user = self.env["res.users"].search(
                [
                    "|",
                    ("caldav_email", "=", organizer_email),
                    ("login", "=", organizer_email),
                ],
                limit=1,
            )
            values["caldav_organizer"] = organizer_email

        values["user_id"] = user.id
        partner_ids.append(user.partner_id.id)
        attendee_values = [{"partner_id": user.partner_id.id, "state": "accepted"}]
        if vevent.get("ATTENDEE"):
            vevent_attendee = vevent["ATTENDEE"]
            if (
                type(vevent_attendee) is not list
            ):  # If there's only one it's not a list 👍
                vevent_attendee = [vevent_attendee]
            for attendee in vevent_attendee:
                partner = self.env["res.partner"].import_caldav_address(attendee)
                attendee_values.append(
                    self.env["calendar.attendee"].caldav_to_odoo(attendee)
                )
                partner_ids.append(partner.id)
        values["attendee_ids"] = [Command.clear()] + [
            Command.create(v) for v in attendee_values
        ]
        values["partner_ids"] = [Command.set(partner_ids)]
        return values

    @api.model
    def _odoo_to_caldav(self, odoo_event):  # Actually a iCal thing, rename?
        if odoo_event.allday:
            start = odoo_event.start_date
            stop = odoo_event.stop_date + timedelta(days=1)
        else:
            start = odoo_event.start.replace(
                tzinfo=timezone.utc
            )  # Make sure CalDAV knows it's a UTC date
            stop = odoo_event.stop.replace(tzinfo=timezone.utc)

        event = Event()
        event.add("SUMMARY", odoo_event.name)
        event.add("DTSTART", start)
        event.add("DTEND", stop)
        event.add("DTSTAMP", fields.Datetime.now().replace(tzinfo=timezone.utc))
        event.add("TRANSP", odoo_event.show_as == "free" and "TRANSPARENT" or "OPAQUE")
        if odoo_event.description:
            event.add("DESCRIPTION", odoo_event.description)
        if odoo_event.location:
            event.add("LOCATION", odoo_event.location)
        if odoo_event.caldav_organizer:
            event.add("ORGANIZER", odoo_event.caldav_organizer)

        if odoo_event.recurrency:
            event.add("RRULE", odoo_event.recurrence_id.to_caldav())

        if odoo_event.exceptions and odoo_event.exceptions.get("dts"):
            for exdate in odoo_event.exceptions["dts"]:
                exdate = fields.Datetime.from_string(exdate)
                exdate = exdate.replace(
                    tzinfo=timezone.utc
                )  # Make sure caldav knows it's UTC
                if odoo_event.allday:
                    event.add("EXDATE", vDDDTypes(exdate.date()))
                else:
                    event.add("EXDATE", exdate)

        attachments = self.env["ir.attachment"].search(
            [
                ("type", "=", "url"),
                ("res_model", "=", "calendar.event"),
                ("res_id", "=", odoo_event.id),
                ("caldav_params", "!=", False),
            ]
        )
        if attachments:
            event.add("ATTACH", attachments.to_caldav())

        alarms = odoo_event.alarm_ids.to_caldav()
        for alarm in alarms:
            event.add_component(alarm)

        attendees = odoo_event.attendee_ids.filtered(
            lambda a: a.partner_id != odoo_event.user_id.partner_id  # Exclude organizer
        )
        if attendees:
            event.add("ATTENDEE", attendees.to_caldav())

        return event

    @api.model_create_multi
    def create(self, vals_list):
        created_events = super().create(vals_list)
        if self.env.context.get("no_caldav"):
            return created_events
        events_to_export = created_events.filtered(
            lambda e: e.caldav_calendar_id
            and (
                not e.recurrency or e.recurrency and e.recurrence_id.base_event_id == e
            )
        )
        for to_export in events_to_export:
            to_export.with_delay(
                identity_key="caldav_export_%s" % to_export.id
            ).create_caldav()
        return created_events

    def create_caldav(self):
        for event in self.filtered(lambda e: not e.caldav_url):
            if not event.caldav_calendar_id:
                raise UserError(_("No CalDAV calendar selected"))
            calendar = event.caldav_calendar_id.get_caldav_object()
            ical_event = self._odoo_to_caldav(event)
            caldav_event = calendar.save_event(ical_event.to_ical())
            event.with_context(no_caldav=True).write(
                {  # Add context to prevent recursion
                    "caldav_url": caldav_event.canonical_url
                }
            )
            # This way the recurrence isn't applied again which will happen with recurrence_update
            if event.recurrency:
                event.recurrence_id.calendar_event_ids.with_context(
                    no_caldav=True
                ).write({"caldav_url": caldav_event.canonical_url})

    def _get_update_future_events_values(self):
        res = super()._get_update_future_events_values()
        res["caldav_url"] = False
        return res

    def write(self, vals):
        if "caldav_calendar_id" in vals and self.filtered(
            lambda e: e.caldav_calendar_id
            and vals["caldav_calendar_id"] != e.caldav_calendar_id.id
        ):
            raise UserError(
                _(
                    "You can't change CalDAV calendar after creation. "
                    "Please instead, delete this event and create a new one with the correct CalDAV calendar."
                )
            )

        res = super().write(vals)
        if self.env.context.get("no_caldav"):
            return res

        # Sync an already created event in Odoo
        to_create = self.filtered(
            lambda e: e.active
            and e.caldav_calendar_id
            and not e.caldav_url
            and (
                not e.recurrency or e.recurrency and e.recurrence_id.base_event_id == e
            )
        )
        for to_export in to_create:
            to_export.with_delay(
                identity_key="caldav_create_%s" % to_export.id
            ).create_caldav()

        to_write = self.filtered(
            lambda e: e.caldav_calendar_id
            and e.caldav_url
            and (
                not e.recurrency or e.recurrency and e.recurrence_id.base_event_id == e
            )
        )
        for to_export in to_write:
            # Splitting events will change the occurrence and archive detached events so in that case we want to update the base_event
            # instead of this one
            if not to_export.active:
                base_event = to_export.recurrence_id.base_event_id
                if not base_event:  # Move this to before write this is not optimal
                    recurrence = self.env["calendar.recurrence"].search(
                        [("base_event_id.caldav_url", "=", to_export.caldav_url)]
                    )
                    if recurrence:
                        base_event = recurrence.base_event_id
                to_export = base_event
            to_export.with_delay().write_caldav()
        return res

    def write_caldav(self):
        # filter should be done somewhere else but when splitting recurrences some "slip" through
        for event in self.filtered(lambda e: e.active and e.caldav_url):
            if not event.caldav_calendar_id:
                raise UserError(_("No CalDAV calendar selected"))
            calendar = event.caldav_calendar_id.get_caldav_object()
            ical_event = self._odoo_to_caldav(event)
            try:
                caldav_event = calendar.event_by_url(event.caldav_url)
                ical_event.add("UID", caldav_event.icalendar_component.get("UID"))
                external_alarms = list(
                    filter(
                        lambda s: type(s) is Alarm
                        and s["ACTION"] not in ("DISPLAY", "AUDIO"),
                        caldav_event.icalendar_component.subcomponents,
                    )
                )
                ical_event.subcomponents += (
                    external_alarms  # Persist alarms we don't want in Odoo
                )
                caldav_event.icalendar_component = ical_event
                caldav_event.save()
            except NotFoundError:
                event.with_context(no_caldav=True).unlink()

    def unlink(self):
        exceptions = []
        deletes = []
        for event in self.filtered(lambda e: e.caldav_calendar_id and e.caldav_url):
            if not event.recurrency:
                # Can't pass event here because the record doesn't exist anymore when the job happens
                deletes.append((event.caldav_calendar_id, event.caldav_url))
            elif len(event.recurrence_id.calendar_event_ids) == 1:
                deletes.append((event.caldav_calendar_id, event.caldav_url))
            elif event.active:
                exceptions.append((event.recurrence_id, event.start))
        res = super().unlink()
        if not self.env.context.get("no_caldav"):
            for ex_date in exceptions:
                recurrence = ex_date[0]
                recurrence.add_exception(ex_date[1])
                recurrence.base_event_id.with_delay().write_caldav()

            for delete in deletes:
                self.with_delay().unlink_caldav(delete[0], delete[1])
        return res

    @api.model
    def unlink_caldav(self, caldav_calendar, caldav_url):
        calendar = caldav_calendar.get_caldav_object()
        try:
            caldav_event = calendar.event_by_url(caldav_url)
            caldav_event.delete()
        except NotFoundError:
            pass  # The event is already deleted
