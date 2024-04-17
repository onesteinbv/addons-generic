# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import ast

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _get_nc_calendar_selection(self):
        nc_calendar_ids = self.nc_calendar_ids or self.env.user.nc_calendar_ids
        values = []
        if nc_calendar_ids:
            [values.append((str(x.id), x.name)) for x in nc_calendar_ids]
        return values

    nc_uid = fields.Char("UID")
    nc_rid = fields.Char("RECURRENCE-ID", compute="_compute_nc_rid", store=True)
    nc_color = fields.Char(string="Color")

    nc_calendar_select = fields.Selection(
        _get_nc_calendar_selection,
        string="Nextcloud Calendar",
        help="Select which Nextcloud Calendar the event will be recorded into",
    )

    nc_calendar_id = fields.Many2one(
        "nc.calendar", "Nextcloud Calendar", compute="_compute_nc_calendar"
    )
    nc_status_id = fields.Many2one("nc.event.status", string="Status")
    nc_calendar_ids = fields.Many2many("nc.calendar", string="Calendars")
    nc_hash_ids = fields.One2many(
        "calendar.event.nchash", "calendar_event_id", "Hash Values"
    )

    nc_require_calendar = fields.Boolean(compute="_compute_nc_require_calendar")
    nc_synced = fields.Boolean("Synced")
    nc_to_delete = fields.Boolean("To Delete")
    nc_allday = fields.Boolean("Nextcloud All day")
    nc_detach = fields.Boolean("Detach from recurring event")
    nc_event_updateable = fields.Boolean(
        "Event Updateable In Nextcloud", compute="_compute_nc_event_updateable"
    )
    nextcloud_event_timezone = fields.Char("Nextcloud Event Timezone")
    nextcloud_calendar_type = fields.Char("Nextcloud Calendar Type")
    nextcloud_rrule = fields.Char("Nextcloud Rrule")

    @api.model
    def default_get(self, fields):
        """
        Inherited odoo base function: Added event status default value
        to 'Confirmed'
        :param fields: Odoo base fields
        :return Super: add changes into this predefined functions
        """
        res = super(CalendarEvent, self).default_get(fields)
        res["nc_status_id"] = self.env.ref(
            "nextcloud_odoo_sync.nc_event_status_confirmed"
        ).id
        return res

    @api.depends(
        "recurrence_id", "allday", "start", "event_tz", "nextcloud_event_timezone"
    )
    def _compute_nc_rid(self):
        """
        This method generates a value for RECURRENCE-ID
        of Nextcloud recurring event
        """
        for event in self:
            if event.recurrence_id:
                if not event.allday:
                    start = event.start
                    tz = event.nextcloud_event_timezone
                    if tz and not event.nc_rid:
                        dt_tz = start.replace(tzinfo=pytz.utc)
                        start = dt_tz.astimezone(pytz.timezone(tz))
                        event.nc_rid = start.strftime("%Y%m%dT%H%M%S")
                    else:
                        event.nc_rid = event.nc_rid or False
                else:
                    event.nc_rid = event.nc_rid or event.start.strftime("%Y%m%d")
            else:
                event.nc_rid = event.nc_rid or False

    @api.depends("nc_calendar_ids")
    def _compute_nc_calendar(self):
        """
        This method computes the value of Nextcloud calendar name to display
        """
        for event in self.sudo().with_context(sync=True):
            calendar = False
            if event.nc_calendar_ids:
                # Get calendar to display on event based on the current user
                calendar_id = event.nc_calendar_ids.filtered(
                    lambda x: x.user_id == self.env.user
                )
                if calendar_id:
                    calendar = calendar_id.ids[0]
            event.nc_calendar_id = calendar
            event.nc_calendar_select = str(calendar) if calendar else False

    @api.depends("nc_calendar_id", "nextcloud_calendar_type")
    def _compute_nc_event_updateable(self):
        for event in self:
            nc_event_updateable = True
            if event.nextcloud_calendar_type:
                nc_event_updateable = False
            elif event.nc_calendar_id:
                default_calendar_id = (
                    self.env["nc.sync.user"]
                    .search(
                        [
                            ("user_id", "=", self.env.user.id),
                            ("sync_calendar", "=", True),
                        ],
                        limit=1,
                    )
                    .mapped("nc_calendar_id")
                )
                if event.nc_calendar_id != default_calendar_id:
                    nc_event_updateable = False
            event.nc_event_updateable = nc_event_updateable

    @api.depends("duration", "partner_ids", "user_id")
    def _compute_nc_require_calendar(self):
        """
        This method determine whether to require a
        value for the Nextcloud calendar
        """
        nc_calendar_ids = self.env.user.nc_calendar_ids
        for event in self:
            if nc_calendar_ids and event.user_id and event.user_id == event.env.user:
                event.nc_require_calendar = True
            else:
                event.nc_require_calendar = False

    @api.onchange("user_id")
    def onchange_nc_user_id(self):
        """
        This method will set the default value of nc_calendar_select
        if the user is required to select a Nextcloud Calendar
        """
        if self.user_id:
            if self.nc_require_calendar:
                default_calendar_id = (
                    self.env["nc.sync.user"]
                    .search(
                        [
                            ("user_id", "=", self.user_id.id),
                            ("sync_calendar", "=", True),
                        ],
                        limit=1,
                    )
                    .mapped("nc_calendar_id")
                )
                if default_calendar_id and self.user_id == self.env.user:
                    self.nc_calendar_select = str(default_calendar_id.id)
            else:
                self.nc_calendar_select = False
                self.nc_calendar_ids = False
        else:
            self.nc_calendar_select = False
            self.nc_calendar_ids = False

    @api.onchange("nc_calendar_select")
    def onchange_nc_calendar_select(self):
        """
        This method ensures that the Nextcloud Calendar stored in the
        nc_calanedar_ids field is updated with the value selected by
        the user in nc_calendar_select and that old values are removed
        """
        if self.nc_require_calendar:
            if self.nc_calendar_select:
                calendar_id = self.env["nc.calendar"].browse(
                    int(self.nc_calendar_select)
                )
            elif not self.nc_calendar_select and self.user_id:
                calendar_id = (
                    self.env["nc.sync.user"]
                    .search(
                        [
                            ("user_id", "=", self.user_id.id),
                            ("sync_calendar", "=", True),
                        ],
                        limit=1,
                    )
                    .mapped("nc_calendar_id")
                )
            else:
                calendar_id = self.env["nc.calendar"]
            new_calendar_ids = []
            if self.nc_calendar_ids:
                new_calendar_ids = self.nc_calendar_ids.ids
                # Get previously linked current user calendar and
                # replace it with the newly selected calendar
                prev_calendar_ids = self.nc_calendar_ids.filtered(
                    lambda x: x.user_id == self.env.user
                )
                if prev_calendar_ids:
                    new_calendar_ids = list(
                        set(new_calendar_ids) - set(prev_calendar_ids.ids)
                    )
            if calendar_id:
                new_calendar_ids.append(calendar_id.id)
                self.nc_calendar_ids = [(6, 0, new_calendar_ids)]

    @api.model
    def create(self, vals):
        """
        Inherited odoo base function
        :params vals: Dictionary of record changes
        :return Super: add changes into this predefined functions
        """
        # Handle untitled event since Nextcloud event
        # can be saved without title
        if "name" not in vals or not vals["name"]:
            vals["name"] = "Untitled event"
        if "allday" in vals:
            vals["nc_allday"] = vals["allday"]
        if "nc_status_id" not in vals or not vals["nc_status_id"]:
            vals["nc_status_id"] = self.env.ref(
                "nextcloud_odoo_sync.nc_event_status_confirmed"
            ).id
        res = super(CalendarEvent, self).create(vals)
        if vals.get("user_id"):
            # Check if a value for calendar exist for the user:
            nc_sync_user_id = self.env["nc.sync.user"].search(
                [("user_id", "=", vals["user_id"]), ("sync_calendar", "=", True)],
                limit=1,
            )
            if "nc_calendar_ids" not in vals or vals["nc_calendar_ids"] == [
                [6, False, []]
            ]:
                if nc_sync_user_id and nc_sync_user_id.nc_calendar_id:
                    res.nc_calendar_ids = [(4, nc_sync_user_id.nc_calendar_id.id)]
            if (
                not self._context.get("sync_from_nextcloud", False)
                and res.nc_calendar_id
                and res.nc_calendar_id != nc_sync_user_id.nc_calendar_id
            ):
                raise UserError(
                    _(
                        "You cannot create nextcloud events for calendars other than default one(%s)",
                        nc_sync_user_id.nc_calendar_id.name,
                    )
                )
        return res

    def write(self, vals):
        """
        Inherited odoo base function
        :params vals: Dictionary of record changes
        :return Super: add changes into this predefined functions
        """

        ex_fields = [
            "nc_uid",
            "nc_rid",
            "nc_hash_ids",
            "nc_synced",
            "nc_to_delete",
            "recurrence_id",
            "nc_calendar_select",
            "nextcloud_event_timezone",
            "nextcloud_rrule",
        ]
        fields_to_update = list(vals.keys())
        calendar_recurrence_obj = self.env["calendar.recurrence"].sudo()
        detach = False
        if not self._context.get("update_recurring", False):
            if not vals.get("recurrence_update", "") in ["future_events", "all_events"]:
                for f in fields_to_update:
                    if f not in ex_fields:
                        detach = True
                        break
            else:
                self = self.with_context(update_recurring=True)
        ex_fields.extend(
            ["nc_allday", "event_tz", "write_date", "nextcloud_calendar_type"]
        )
        ex_fields.remove("nc_to_delete")
        record_updated = False
        for f in fields_to_update:
            if f not in ex_fields:
                record_updated = True
                break
        if (
            not self._context.get("sync", False)
            and "nc_synced" not in vals
            and record_updated
            and not self._context.get("update_recurring", False)
        ):
            vals["nc_synced"] = False
        if (
            self._context.get("update_recurring", False)
            and len(self.ids) == 1
            and self.ids == [self.recurrence_id.base_event_id.id]
        ):
            vals["nc_synced"] = False
            if not self._context.get("update_nc_rid", False):
                if not self.allday:
                    start = self.start
                    tz = self.nextcloud_event_timezone
                    if tz:
                        dt_tz = start.replace(tzinfo=pytz.utc)
                        start = dt_tz.astimezone(pytz.timezone(tz))
                        nc_rid = start.strftime("%Y%m%dT%H%M%S")
                    else:
                        nc_rid = self.nc_rid
                else:
                    nc_rid = self.start.strftime("%Y%m%d")
                vals["nc_rid"] = nc_rid
        if vals.get("recurrence_update") == "future_events":
            for record in self:
                record.recurrence_id.base_event_id.sudo().write(
                    {"nc_synced": False, "nc_uid": False, "nc_hash_ids": [(6, 0, [])]}
                )
        for record in self:
            # Detach the record from recurring event whenever an edit was made
            # to make it compatible when synced to Nextcloud calendar
            if (
                not self._context.get("sync_from_nextcloud", False)
                and detach
                and record.nc_uid
                and record.user_id
                and record.user_id != self.env.user
            ):
                raise UserError(
                    _("You cannot update nextcloud events if you are not the organizer")
                )
            if (
                not self._context.get("sync_from_nextcloud", False)
                and not record.nc_event_updateable
                and detach
            ):
                if record.nextcloud_calendar_type:
                    raise UserError(
                        _("You cannot update nextcloud events for Birthday calendars")
                    )
                default_calendar_id = (
                    self.env["nc.sync.user"]
                    .search(
                        [
                            ("user_id", "=", self.env.user.id),
                            ("sync_calendar", "=", True),
                        ],
                        limit=1,
                    )
                    .mapped("nc_calendar_id")
                )
                raise UserError(
                    _(
                        "You cannot update nextcloud events for calendars other than default one(%s)",
                        default_calendar_id.name,
                    )
                )
            if not self._context.get("sync_from_nextcloud"):
                if "active" in vals and not vals.get("active"):
                    new_recurrence = calendar_recurrence_obj.search(
                        [("base_event_id", "=", record.id)], limit=1
                    )
                    if new_recurrence:
                        new_recurring_events = new_recurrence.calendar_event_ids.sorted(
                            key=lambda r: r.start
                        )
                        if new_recurring_events:
                            new_recurrence.base_event_id = new_recurring_events[0].id
                            hash_vals_list = []
                            for rec in record.nc_hash_ids:
                                hash_vals_list.append(
                                    (
                                        0,
                                        0,
                                        {
                                            "nc_sync_user_id": rec.nc_sync_user_id.id,
                                            "nc_event_hash": rec.nc_event_hash,
                                        },
                                    )
                                )
                            new_recurring_events.write(
                                {"nc_hash_ids": hash_vals_list, "nc_synced": True}
                            )
                            new_recurring_events[0].write({"nc_synced": False})
            if record.recurrence_id:
                if detach:
                    vals.update({"nc_detach": True})
        return super(CalendarEvent, self).write(vals)

    def unlink(self):
        """
        We can"t delete an event that is also in Nextcloud Calendar.
        Otherwise we would have no clue that the event must must deleted
        from Nextcloud Calendar at the next sync. We just mark the event as to
        delete (nc_to_delete=True) before we sync.
        """
        has_nc_uids = self.env["calendar.event"]
        if not self._context.get("force_delete", False):
            for record in self:
                if record.nc_uid and record.user_id and record.user_id != self.env.user:
                    raise UserError(
                        _(
                            "You cannot delete nextcloud events if you are not the organizer"
                        )
                    )
            default_calendar_id = (
                self.env["nc.sync.user"]
                .search(
                    [("user_id", "=", self.env.user.id), ("sync_calendar", "=", True)],
                    limit=1,
                )
                .mapped("nc_calendar_id")
            )
            has_nc_uids = self.filtered(
                lambda r: r.nc_uid and r.nc_calendar_id == default_calendar_id
            )
            if has_nc_uids:
                has_nc_uids.write({"nc_to_delete": True})
        for record in self:
            if record.recurrence_id:
                nc_exdates = (
                    ast.literal_eval(str(record.recurrence_id.nc_exdate))
                    if record.recurrence_id.nc_exdate
                    else []
                )
                if record.nc_rid:
                    nc_exdates.append(record.nc_rid)
                    record.recurrence_id.write({"nc_exdate": nc_exdates})
        self = self - has_nc_uids
        return super(CalendarEvent, self).unlink()


class CalendarEventNchash(models.Model):
    _name = "calendar.event.nchash"
    _description = "Calendar Event Nextcloud Hash"

    calendar_event_id = fields.Many2one(
        "calendar.event", "Calendar Event", ondelete="cascade"
    )
    user_id = fields.Many2one(
        "res.users", "Odoo User", related="nc_sync_user_id.user_id", store=True
    )
    nc_sync_user_id = fields.Many2one("nc.sync.user", "Sync User", ondelete="cascade")
    nc_uid = fields.Char("UID", related="calendar_event_id.nc_uid", store=True)
    nc_event_hash = fields.Char("Event Hash")
