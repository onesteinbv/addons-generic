from datetime import datetime
from unittest.mock import MagicMock, patch

from caldav.objects import Calendar, Event

from odoo.tests.common import TransactionCase
from odoo.tools import html2plaintext


class TestSyncNextcloud(TransactionCase):
    def assertNextcloudEventCreated(self, od_values):
        kwrags = Calendar.save_event.call_args.kwargs
        expected_args = self.from_odoo_to_nc_format_dict(list(kwrags), od_values[0])
        self.assertEqual(kwrags, expected_args)

    @patch("caldav.DAVClient")
    def get_params(self, mock_client):
        mock_dav_client = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_dav_client
        mock_principal = MagicMock()
        mock_dav_client.principal.return_value = mock_principal
        params = {
            "log_obj": self.create_log(),
            "all_odoo_event_ids": self.env["calendar.event"].search([]),
            "all_nc_calendar_ids": self.env["nc.calendar"].search(
                [("user_id", "!=", False)]
            ),
            "all_user_ids": self.env["res.users"].search([]),
            "all_sync_user_ids": self.env["nc.sync.user"].search([]),
            "all_partner_ids": self.env["res.partner"].search([("email", "!=", False)]),
            "all_odoo_event_type_ids": self.env["calendar.event.type"].search([]),
            "status_vals": {
                "confirmed": self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_confirmed"
                ).id,
                "tentative": self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_tentative"
                ).id,
                "cancelled": self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_canceled"
                ).id,
            },
            "create_count": 0,
            "write_count": 0,
            "delete_count": 0,
            "error_count": 0,
            "connection": mock_dav_client,
            "principal": mock_principal,
            "nc_user_ids": False,
        }
        od_events = {
            "nc_uid": False,
            "od_event": self.create_odoo_event(),
            "event_hash": False,
        }
        return {
            "sync_user_id": self.create_nc_sync_user(),
            "nc_events_dict": {"create": [od_events], "write": [], "delete": []},
            "params": params,
        }

    @patch("caldav.DAVClient")
    def create_nextclound_event_allday(self, mock_client):
        data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//IDN nextcloud.com//Calendar app 4.2.4//EN
BEGIN:VEVENT
UID:20230505T051435-1234567890@example.com
DTSTART;VALUE=DATE:20230505
DTEND;VALUE=DATE:20230506
DTSTAMP:20230505T051443Z
STATUS:CONFIRMED
SUMMARY:Test all day
DESCRIPTION:This is a test event.
END:VEVENT
END:VCALENDAR"""
        calendar = Calendar(
            client=mock_client, url="http://example.com", parent=None, name="Personal"
        )
        event = Event(
            client=mock_client, url="http://example.com", data=data, parent=calendar
        )
        return event

    @patch("caldav.DAVClient")
    def create_nextcloud_event(self, mock_client):
        data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp.//CalDAV Client//EN
BEGIN:VEVENT
UID:20190905T090000-1234567890@example.com
DTSTAMP:20190905T120000Z
DTSTART:20190905T090000Z
DTEND:20190905T100000Z
SUMMARY:Test Event
DESCRIPTION:This is a test event.
LOCATION:Test Location
END:VEVENT
END:VCALENDAR"""
        calendar = Calendar(
            client=mock_client, url="http://example.com", parent=None, name="Personal"
        )
        event = Event(
            client=mock_client, url="http://example.com", data=data, parent=calendar
        )
        return event

    def create_odoo_event(self):
        calendar_event = self.env["calendar.event"]
        return calendar_event.create(
            {
                "name": "Test Event",
                "start": "2019-09-05 09:00",
                "stop": "2019-09-05 10:00",
                "description": "This is a test event.",
                "location": "Test Location",
                "user_id": 2,
            }
        )

    def create_log(self):
        datetime_now = datetime.now()
        return self.env["nc.sync.log"].create(
            {
                "name": datetime_now.strftime("%Y%m%d-%H%M%S"),
                "date_start": datetime_now,
                "state": "connecting",
                "next_cloud_url": "test nc url",
                "odoo_url": "test odoo url",
            }
        )

    def create_nc_calendar(self):
        calendar_obj = self.env["nc.calendar"]
        nc_calendar_id = calendar_obj.create({"name": "Test Calendar", "user_id": 2})
        return nc_calendar_id.id

    def create_nc_sync_user(self):
        sync_user_obj = self.env["nc.sync.user"]
        sync_user_id = sync_user_obj.create(
            {
                "name": "test_sync_common_user",
                "user_name": "test_sync_common_user",
                "nc_password": "testpw",
                "user_id": 2,
                "nc_calendar_id": self.create_nc_calendar(),
            }
        )
        return sync_user_id

    def from_odoo_to_nc_format_dict(self, keys, od_event):
        nextcloud_caldav_obj = self.env["nextcloud.caldav"]
        field_mapping = nextcloud_caldav_obj.get_caldav_fields()
        result = {}
        for k in keys:
            key = field_mapping[k]
            if k in ("dtstart", "dtend"):
                val = nextcloud_caldav_obj.convert_date(
                    od_event[key], "Europe/Amsterdam", "local"
                )
                result[k] = val
            elif k == "description":
                result[k] = html2plaintext(od_event[key])
            elif k == "status" and od_event[key]:
                result[k] = od_event[key][1].upper()
            elif k == "transp":
                show_as = {"free": "TRANSPARENT", "busy": "OPAQUE"}
                result[k] = show_as[od_event[key]]
            else:
                result[k] = od_event[key]
        return result
