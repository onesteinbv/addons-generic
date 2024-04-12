# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import common
from unittest.mock import patch, MagicMock
from caldav.objects import Event, Calendar


class TestNextCloudConfig(common.TransactionCase):
    # def test_nextcloud_config(self):
    #     config_obj = self.env["ir.config_parameter"]
    #     self.assertEqual(
    #         config_obj.sudo().get_param(
    #             "nextcloud_odoo_sync.nextcloud_connection_status"
    #         ),
    #         False,
    #     )
    #     config_obj.sudo().set_param(
    #         "nextcloud_odoo_sync.nextcloud_connection_status", "online"
    #     )
    #     self.assertEqual(
    #         config_obj.sudo().get_param(
    #             "nextcloud_odoo_sync.nextcloud_connection_status"
    #         ),
    #         "online",
    #     )
    #     config_obj.sudo().set_param(
    #         "nextcloud_odoo_sync.nextcloud_connection_status", False
    #     )

    @patch("odoo.addons.nextcloud_odoo_sync.models.nc_calendar.NcCalendar")
    def create_nc_calendar(self, mock_calendar_obj):
        nc_calendar_id = mock_calendar_obj.create({"name": "Personal", "user_id": 2})
        return nc_calendar_id.id

    @patch("caldav.DAVClient")
    def test_event_record(self, mock_client):
        data = """
BEGIN:VCALENDAR
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
END:VCALENDAR
        """
        calendar = Calendar(
            client=mock_client, url="http://example.com", parent=None, name="Personal"
        )
        event = Event(
            client=mock_client, url="http://example.com", data=data, parent=calendar
        )
        print(event)

    @patch("caldav.DAVClient")
    def test_successful_connection(self, mock_client):
        # Mock the DAVClient object and the principal object
        nextcloud_caldav_obj = self.env["nextcloud.caldav"]
        mock_dav_client = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_dav_client
        mock_principal = MagicMock()
        mock_dav_client.principal.return_value = mock_principal

        # Call the check_nextcloud_connection method with a URL, username, and
        # password
        url = "http://example.com"
        username = "test_user"
        password = "test_password"
        client, principal = nextcloud_caldav_obj.check_nextcloud_connection(
            url, username, password
        )

        # Assert that the DAVClient object was created with the correct URL,
        # username, and password
        mock_client.assert_called_once_with(
            url=url, username=username, password=password
        )

        # Assert that the principal method was called on the DAVClient object
        mock_dav_client.principal.assert_called_once()

        # Assert that the return values are the mocked client and principal
        # objects
        self.assertEqual(client, mock_dav_client)
        self.assertEqual(principal, mock_principal)
