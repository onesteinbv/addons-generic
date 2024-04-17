# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


import hashlib
import json
from datetime import date, datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.nextcloud_odoo_sync.models import jicson


class NcSyncUser(models.Model):
    _name = "nc.sync.user"
    _inherit = ["nextcloud.caldav"]
    _description = "Nextcloud Sync User"

    name = fields.Char("Odoo Username", related="user_id.name")
    nextcloud_user_id = fields.Char("Nextcloud User ID")
    user_name = fields.Char("Username", required=True)
    nc_password = fields.Char("Password", required=True)
    user_message = fields.Char(
        default="'Default Calendar' field will be used"
        "as your default Nextcloud calendar when "
        "creating new events in Odoo"
    )

    user_id = fields.Many2one(
        "res.users", "Odoo User", required=True, default=lambda self: self.env.user.id
    )
    partner_id = fields.Many2one(
        "res.partner", "Partner", related="user_id.partner_id", store=True
    )
    nc_calendar_id = fields.Many2one(
        "nc.calendar",
        "Default Calendar",
        help="Allows 2 way syncing with this calendar",
    )
    nc_calendar_ids = fields.Many2many(
        "nc.calendar",
        "nc_sync_user_nc_calendar_rel",
        "sync_user_id",
        "nc_calendar_id",
        string="Show Other Calendars",
    )
    nc_hash_ids = fields.One2many(
        "calendar.event.nchash", "nc_sync_user_id", "Hash Values"
    )

    user_has_calendar = fields.Boolean(
        "User has calendar", compute="compute_user_has_calendar"
    )
    sync_calendar = fields.Boolean("Sync Calendar")
    nc_email = fields.Char("Email")
    start_date = fields.Date("Sync Events From This Date", default=date.today())
    nextcloud_url = fields.Char(string="Server URL", required=True)

    @api.depends("user_id", "user_name", "nc_password")
    def compute_user_has_calendar(self):
        """
        This method determine if current Odoo user
        have Nextcloud calendar records
        """
        for user in self:
            user.user_has_calendar = (
                True if user.user_id and user.user_id.nc_calendar_ids else False
            )

    @api.constrains("user_id", "user_name")
    def check_user_exist(self):
        """
        Checks if user information is already exists
        :return error if record already exist
        """
        for user in self:
            sync_user_id = self.search(
                [
                    "&",
                    ("id", "!=", user.id),
                    "|",
                    ("user_id", "=", user.user_id.id),
                    ("user_name", "=ilike", user.user_name),
                ],
                limit=1,
            )
            if sync_user_id:
                raise ValidationError(
                    _(
                        "Existing configuration found. The selected Odoo User '%s'"
                        " or Nextcloud Username '%s' is already mapped to an"
                        " existing record" % (user.user_id.name, user.user_name)
                    )
                )

    @api.onchange("nc_calendar_id", "nc_email")
    def onchange_nc_calendar_id(self):
        """
        Update user message upon changing nextclound calenda
        """
        if self.nc_calendar_id:
            self.user_message = (
                "%s will be used as your default Odoo "
                "calendar when creating new events"
            ) % self.nc_calendar_id.name
            if self.nc_email:
                self.sync_calendar = True
            if self.nc_calendar_id.id in self.nc_calendar_ids.ids:
                self.nc_calendar_ids = [(3, self.nc_calendar_id.id)]
        else:
            self.sync_calendar = False
            self.user_message = (
                "'Default Calendar' field will be used as "
                "your default odoo calendar when creating "
                "new events"
            )

    @api.onchange("nc_calendar_ids")
    def onchange_nc_calendar_ids(self):
        if self.nc_calendar_id.id in self.nc_calendar_ids.ids:
            self.nc_calendar_ids = [(3, self.nc_calendar_id.id)]

    @api.model
    def create(self, vals):
        if vals.get("nextcloud_url", False):
            vals["nextcloud_url"] = vals["nextcloud_url"].strip("/")
        return super(NcSyncUser, self).create(vals)

    def write(self, vals):
        """
        Inherited odoo base function
        :param vals: Dictionary of record changes
        :return add changes into this predefined functions
        """
        nc_calendar_ids = []
        calendar_event_obj = self.env["calendar.event"]
        if (
            vals.get("user_name")
            or vals.get("nc_password")
            or vals.get("nextcloud_url", False)
            or vals.get("sync_calendar")
        ):
            nextcloud_caldav_obj = self.env["nextcloud.caldav"]
            for record in self:
                nc_url = (
                    vals.get("nextcloud_url", "").strip("/")
                    if vals.get("nextcloud_url")
                    else record.nextcloud_url
                ) + "/remote.php/dav"
                username = vals.get("user_name", False) or record.user_name
                nc_password = vals.get("nc_password", False) or record.nc_password
                connection, principal = nextcloud_caldav_obj.check_nextcloud_connection(
                    url=nc_url, username=username, password=nc_password
                )
                if isinstance(principal, dict):
                    sync_error = principal["sync_error_id"].name
                    response = principal["response_description"]
                    raise ValidationError(f"{sync_error}: {response}")
        if "nc_calendar_id" in vals:
            calendar_event_ids = calendar_event_obj.search(
                [
                    "|",
                    ("user_id", "=", self.user_id.id),
                    ("partner_ids", "in", self.user_id.partner_id.id),
                    ("nc_synced", "=", False),
                ]
            ).filtered(
                lambda x: (not x.nc_calendar_ids)
                and x.start
                >= datetime.combine(
                    self.start_date or date.today(), datetime.min.time()
                )
            )
            # calendar_ids = calendar_event_ids.nc_calendar_ids.filtered(
            #     lambda x: x.user_id == self.user_id
            # )
            # for calendar_id in calendar_ids:
            #     calendar_event_ids.nc_calendar_ids = [(3, calendar_id.id)]
            calendar_event_ids.with_context(sync=True).write(
                {"nc_calendar_ids": [(4, vals["nc_calendar_id"])]}
            )
        if vals.get("nextcloud_url", False):
            vals["nextcloud_url"] = vals["nextcloud_url"].strip("/")
        if vals.get("nc_calendar_ids"):
            nc_calendar_ids = self.nc_calendar_ids
        res = super(NcSyncUser, self).write(vals)
        if vals.get("nc_calendar_ids"):
            for record in self:
                for rec in nc_calendar_ids:
                    if (
                        rec not in record.nc_calendar_ids
                        and rec != record.nc_calendar_id
                    ):
                        calendar_event_obj.search(
                            [
                                ("partner_ids", "in", record.user_id.partner_id.id),
                                ("nc_uid", "!=", False),
                            ]
                        ).filtered(
                            lambda x: len(x.nc_calendar_ids) == 1
                            and rec in x.nc_calendar_ids
                        ).with_context(
                            force_delete=True
                        ).unlink()
        return res

    def unlink(self):
        """
        Inherited odoo base function
        :return add changes into this predefined functions
        """
        calendar_event_obj = self.env["calendar.event"]
        calendar_event_hash_obj = self.env["calendar.event.nchash"]
        for record in self.filtered(lambda x: x.user_id):
            calendar_event_hash_obj.search(
                [("nc_sync_user_id", "=", record.id)]
            ).unlink()
            calendar_ids = calendar_event_obj.search(
                [("user_id", "=", record.user_id.id)]
            )
            calendar_ids.filtered(lambda x: not x.nc_hash_ids).write(
                {"nc_uid": False, "nc_synced": False}
            )
            # Remove all Nextcloud calendar records
            record.user_id.nc_calendar_ids.unlink()
        return super(NcSyncUser, self).unlink()

    def save_user_config(self):
        """
        Returns calendar event action. Close the pop-up and display the
        calendar event records
        :return calendar event action
        """
        return self.env.ref("calendar.action_calendar_event").sudo().read()[0]

    def get_user_connection(self):
        nc_url = self.nextcloud_url + "/remote.php/dav"
        connection, principal = self.env["nextcloud.caldav"].check_nextcloud_connection(
            url=nc_url, username=self.user_name, password=self.nc_password
        )
        if isinstance(principal, dict):
            sync_error = principal["sync_error_id"].name
            response = principal["response_description"]
            raise ValidationError(f"{sync_error}: {response}")
        user_data = self.env["nextcloud.base"].get_user(
            principal.client.username,
            self.nextcloud_url,
            self.user_name,
            self.nc_password,
        )
        self.nc_email = user_data.get("email", False) if user_data else False
        return {"connection": connection, "principal": principal}

    def get_user_calendars(self, principal):
        """
        This method gets all the calendar records of the
        Nextcloud user and create it in Odoo if not exist
        :param connection: CalDav connection principal object
        """
        nc_calendars = principal.calendars()
        nc_calendars = [
            cal for cal in nc_calendars if "shared_by" not in cal.canonical_url
        ]
        # Remove Nextcloud calendars in Odoo if the canonical URL
        # no longer exist in Nextcloud
        nc_calendar_obj = self.env["nc.calendar"]
        calendar_not_in_odoo_ids = nc_calendar_obj.search(
            [
                (
                    "calendar_url",
                    "not in",
                    [str(x.canonical_url) for x in nc_calendars],
                ),
                ("user_id", "=", self.user_id.id),
            ]
        )
        if calendar_not_in_odoo_ids:
            calendar_not_in_odoo_ids.sudo().unlink()
        result = []
        nc_calendar_ids = nc_calendar_obj.search([("user_id", "=", self.user_id.id)])
        for record in nc_calendars:
            nc_calendar_id = nc_calendar_ids.filtered(
                lambda x: x.name == record.name
                and x.calendar_url == record.canonical_url
            )
            if not nc_calendar_id:
                result.append(
                    {
                        "name": record.name,
                        "user_id": self.user_id.id,
                        "calendar_url": record.canonical_url,
                    }
                )
        if result:
            self.env["nc.calendar"].sudo().create(result)

    def check_nc_connection(self):
        """
        This method connects to Nextcloud server using the
        username and password provided for the user and
        triggers the creation of Nextcloud Calendar record
        for use in creating events in Odoo
        :return Dictionary, odoo action
        """
        connection_dict = self.sudo().get_user_connection()
        principal = connection_dict.get("principal", False)
        self.get_user_calendars(principal)
        if not self.nc_calendar_id and self.user_id.nc_calendar_ids:
            self.nc_calendar_id = self.user_id.nc_calendar_ids[0]
        target = "new" if self._context.get("pop_up") else "main"
        res = {
            "name": "NextCloud User Setup",
            "view_mode": "form",
            "res_model": "nc.sync.user",
            "type": "ir.actions.act_window",
            "target": target,
            "res_id": self.id,
        }
        if target == "main":
            res.update(
                {"context": {"form_view_initial_mode": "edit", "no_footer": True}}
            )
        return res

    def get_event_data(self, event):
        """
        This method returns the following data of an event:
        UID, hash, dictionary of event values
        :param event: Calendar event object
        :return dictionary of event values
        """
        event_vals = jicson.fromText(event.data).get("VCALENDAR")[0].get("VEVENT")
        data = []
        nc_uid = False
        # Remove the DTSTAMP values as it always changes
        # when event get queried from Nextcloud
        for d in event_vals:
            nc_uid = d["UID"]
            d.pop("DTSTAMP")
            d.pop("SEQUENCE", False)
            exdate_key = [k for k, v in d.items() if "EXDATE" in k]
            vevent = event.vobject_instance.vevent
            if isinstance(vevent.dtstart.value, datetime):
                date_format = "%Y%m%dT%H%M%S"
            else:
                date_format = "%Y%m%d"
            if exdate_key:
                tz = False
                if "TZID" in exdate_key[0]:
                    tz = exdate_key[0].split("=")[1]
                d.pop(exdate_key[0])
                d["exdates"] = [
                    x.value[0].strftime(date_format) for x in vevent.exdate_list
                ]
                d["exdate_tz"] = tz
            data.append(d)
        vals = {"data": data}
        vals["uid"] = nc_uid
        json_data = str(json.dumps(vals["data"], sort_keys=True)).encode("utf-8")
        vals["hash"] = hashlib.sha1(json_data).hexdigest()
        return vals

    def get_all_user_events(self, **params):
        """
        This method get all user events in both Odoo and Nextcloud
        :param log_id: single recordset of nc.sync.log model
        :params **params: dictionary of multiple recordsets
                from different models
        :return Dictionary of odoo and nextcloud events
        """
        events = params["all_odoo_event_ids"]
        log_obj = params["log_obj"]
        result = {
            "od_events": [],
            "nc_events": [],
            "connection": False,
            "principal": False,
        }
        for user in self:
            start_date = datetime.combine(
                self.start_date or date.today(), datetime.min.time()
            )
            if not events:
                events = (
                    self.env["calendar.event"]
                    .sudo()
                    .search([("start", ">=", start_date)], order="start")
                )
            try:
                connection_dict = self.get_user_connection()
                principal = connection_dict.get("principal", False)
                result["principal"] = principal
                result["connection"] = connection_dict.get("connection", False)
                self.get_user_calendars(principal)
            except Exception as error:
                if log_obj:
                    log_obj.log_event("error", error=error, message="Nextcloud:")
                    return result
                else:
                    raise ValidationError(_(error))
            if not self.nc_calendar_id:
                error = "Default Calendar is deleted from Nextcloud"
                if log_obj:
                    log_obj.log_event("error", error=error, message="Nextcloud:")
                    return result
                else:
                    raise ValidationError(_(error))
            try:
                # Get all Odoo events where user is organizer or attendee
                od_event_ids = events.filtered(
                    lambda x: x.user_id == user.user_id
                    or (x.partner_ids and user.partner_id in x.partner_ids)
                )
                for event in od_event_ids:
                    # if event is not yet syned into nextcloud but the current
                    # sync user is only an attendee of the event then the event
                    # should not be created in nextcloud since it will
                    # be automatically created by the event organizer
                    if (
                        event.user_id in params["all_sync_user_ids"].mapped("user_id")
                        and not event.nc_uid
                        and event.user_id != user.user_id
                    ):
                        continue
                    event_hash = False
                    if event.nc_hash_ids:
                        event_hash = event.nc_hash_ids.filtered(
                            lambda x: x.nc_sync_user_id == user
                        ).mapped("nc_event_hash")
                    result["od_events"].append(
                        {
                            "nc_uid": event.nc_uid,
                            "od_event": event,
                            "event_hash": event_hash[0] if event_hash else False,
                        }
                    )
                    if (
                        event.recurrence_id
                        and event.recurrence_id.base_event_id not in od_event_ids
                    ):
                        event_hash = False
                        base_event = event.recurrence_id.base_event_id
                        if base_event.nc_hash_ids:
                            event_hash = base_event.nc_hash_ids.filtered(
                                lambda x: x.nc_sync_user_id == user
                            ).mapped("nc_event_hash")
                        result["od_events"].append(
                            {
                                "nc_uid": base_event.nc_uid,
                                "od_event": base_event,
                                "event_hash": event_hash[0] if event_hash else False,
                            }
                        )

                # Get all Nextcloud events of the user
                nc_calendar_obj = self.env["nc.calendar"]
                for calendar in principal.calendars():
                    # Check if calendar exist for the user and make sure
                    # it has the same name as the Nextcloud calendar in case
                    # the user rename it in Nextcloud, otherwise create a new
                    # calendar if not exist
                    if "shared_by" in calendar.canonical_url:
                        continue
                    nc_calendar_id = nc_calendar_obj.search(
                        [
                            ("user_id", "=", self.user_id.id),
                            ("calendar_url", "=", calendar.canonical_url),
                        ],
                        limit=1,
                    )
                    if nc_calendar_id:
                        if calendar.name != nc_calendar_id.name:
                            nc_calendar_id.name = calendar.name
                    else:
                        nc_calendar_obj.sudo().create(
                            {
                                "name": calendar.name,
                                "user_id": user.user_id.id,
                                "calendar_url": calendar.canonical_url,
                            }
                        )
                        continue
                    if (
                        calendar.canonical_url
                        not in self.nc_calendar_ids.mapped("calendar_url")
                        and not calendar.canonical_url
                        == self.nc_calendar_id.calendar_url
                    ):
                        continue
                    events_fetched = calendar.search(
                        start=start_date,
                        event=True,
                    )
                    for item in events_fetched:
                        event_vals = user.get_event_data(item)
                        result["nc_events"].append(
                            {
                                "nc_uid": event_vals["uid"],
                                "event_hash": event_vals["hash"],
                                "nc_event": event_vals["data"],
                                "nc_caldav": item,
                            }
                        )
                return result
            except Exception as error:
                if log_obj:
                    log_obj.log_event("error", error=error, message="Nextcloud:")
                    return result
                else:
                    raise ValidationError(_(error))

    def check_nc_event_organizer(self, caldav_event):
        """
        Checks if nextcloud organizer is the same with odoo email
        :param caldav_event: Caldav event data
        :return Boolean
        """
        if "organizer" in caldav_event.instance.vevent.contents:
            organizer_email = caldav_event.instance.vevent.organizer.value.replace(
                "mailto:", ""
            )
            if organizer_email == self.nc_email:
                return True
            else:
                return False
        return True

    def get_nc_event_hash_by_uid(self, nc_uid):
        """
        Check and get nextcloud event hash using UID
        :param nc_uid: string, Nextcloud UID
        :return Event hash
        """
        nc_calendar_obj = self.env["nc.calendar"]
        for user in self:
            connection_dict = user.get_user_connection()
            principal = connection_dict["principal"]
            for calendar in principal.calendars():
                # Check if calendar exist for the user and make sure
                # it has the same name as the Nextcloud calendar in case
                # the user rename it in Nextcloud, otherwise create a new
                # calendar if not exist
                if "shared_by" in calendar.canonical_url:
                    continue
                nc_calendar_id = nc_calendar_obj.search(
                    [
                        ("user_id", "=", self.user_id.id),
                        ("calendar_url", "=", calendar.canonical_url),
                    ],
                    limit=1,
                )
                if nc_calendar_id:
                    if calendar.name != nc_calendar_id.name:
                        nc_calendar_id.name = calendar.name
                else:
                    return False
                if (
                    calendar.canonical_url
                    not in self.nc_calendar_ids.mapped("calendar_url")
                    and not calendar.canonical_url == self.nc_calendar_id.calendar_url
                ):
                    continue
                start_date = datetime.combine(
                    self.start_date or date.today(), datetime.min.time()
                )
                events_fetched = calendar.search(
                    start=start_date,
                    event=True,
                )
                for item in events_fetched:
                    event_vals = user.get_event_data(item)
                    if event_vals["uid"] == nc_uid:
                        return event_vals["hash"]
        return False

    def get_nc_event_hash_by_uid_for_other_user(self, nc_uid):
        """
        Check and get nextcloud event hash using UID
        :param nc_uid: string, Nextcloud UID
        :return Event hash, Calendar
        """
        nc_calendar_obj = self.env["nc.calendar"]
        for user in self:
            connection_dict = user.get_user_connection()
            principal = connection_dict["principal"]
            for calendar in principal.calendars():
                # Check if calendar exist for the user and make sure
                # it has the same name as the Nextcloud calendar in case
                # the user rename it in Nextcloud, otherwise create a new
                # calendar if not exist
                if "shared_by" in calendar.canonical_url:
                    continue
                nc_calendar_id = nc_calendar_obj.search(
                    [
                        ("user_id", "=", self.user_id.id),
                        ("calendar_url", "=", calendar.canonical_url),
                    ],
                    limit=1,
                )
                if nc_calendar_id:
                    if calendar.name != nc_calendar_id.name:
                        nc_calendar_id.name = calendar.name
                else:
                    return False, False
                if (
                    calendar.canonical_url
                    not in self.nc_calendar_ids.mapped("calendar_url")
                    and not calendar.canonical_url == self.nc_calendar_id.calendar_url
                ):
                    continue
                start_date = datetime.combine(
                    self.start_date or date.today(), datetime.min.time()
                )
                events_fetched = calendar.search(
                    start=start_date,
                    event=True,
                )
                for item in events_fetched:
                    event_vals = user.get_event_data(item)
                    if event_vals["uid"] == nc_uid:
                        return event_vals["hash"], nc_calendar_id
        return False, False
