# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
from datetime import datetime
from os.path import dirname, join

from vcr import VCR

from odoo.tests import common

logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "vcr_cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
)


class TestCommon(common.TransactionCase):
    def setUp(self):
        super(TestCommon, self).setUp()

        # prepare users
        self.organizer_user = self.env["res.users"].search([("name", "=", "test")])
        if not self.organizer_user:
            partner = self.env["res.partner"].create(
                {"name": "test", "email": "test@example.com"}
            )
            self.organizer_user = self.env["res.users"].create(
                {
                    "name": "test",
                    "login": "test@example.com",
                    "partner_id": partner.id,
                }
            )
        #
        self.attendee_user = self.env["res.users"].search(
            [("name", "=", "John Attendee")]
        )
        if not self.attendee_user:
            partner = self.env["res.partner"].create(
                {"name": "John Attendee", "email": "john@attendee.com"}
            )
            self.attendee_user = self.env["res.users"].create(
                {
                    "name": "John Attendee",
                    "login": "john@attendee.com",
                    "partner_id": partner.id,
                }
            )

        # -----------------------------------------------------------------------------------------
        # To create Odoo events
        # -----------------------------------------------------------------------------------------
        self.start_date = datetime(2023, 8, 22, 10, 0, 0, 0)
        self.end_date = datetime(2021, 8, 22, 11, 0, 0, 0)

        # simple event values to create a Odoo event
        self.simple_event_values = {
            "name": "simple_event",
            "description": "my simple event",
            "active": True,
            "start": self.start_date,
            "stop": self.end_date,
            "partner_ids": [
                (4, self.organizer_user.partner_id.id),
                (4, self.attendee_user.partner_id.id),
            ],
        }
        self.recurrent_event_values = {
            "name": "recurring_event",
            "description": "a recurring event",
            "partner_ids": [(4, self.attendee_user.partner_id.id)],
            "recurrency": True,
            "follow_recurrence": True,
            "start": self.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "stop": self.end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "event_tz": "Europe/Amsterdam",
            "recurrence_update": "self_only",
            "rrule_type": "daily",
            "end_type": "forever",
            "duration": 1,
        }

    def create_events_for_tests(self):
        """
        Create some events for test purpose
        """

        # ---- create some events that will be updated during tests -----

        # a simple event
        self.simple_event = self.env["calendar.event"].search(
            [("name", "=", "simple_event")]
        )
        if not self.simple_event:
            self.simple_event = (
                self.env["calendar.event"]
                .with_user(self.organizer_user)
                .create(
                    dict(
                        self.simple_event_values,
                    )
                )
            )

        # a recurrent event with 7 occurrences
        self.recurrent_base_event = self.env["calendar.event"].search(
            [("name", "=", "recurrent_event")],
            order="id",
            limit=1,
        )
        already_created = self.recurrent_base_event

        if not already_created:
            self.recurrent_base_event = (
                self.env["calendar.event"]
                .with_user(self.organizer_user)
                .create(self.recurrent_event_values)
            )
        self.recurrence = self.env["calendar.recurrence"].search(
            [("base_event_id", "=", self.recurrent_base_event.id)]
        )
        self.recurrent_events = self.recurrence.calendar_event_ids.sorted(
            key=lambda r: r.start
        )
        self.recurrent_events_count = len(self.recurrent_events)

    def assert_odoo_event(self, odoo_event, expected_values):
        """
        Assert that an Odoo event has the same values than in the expected_values dictionary,
        for the keys present in expected_values.
        """
        self.assertTrue(expected_values)

        odoo_event_values = odoo_event.read(list(expected_values.keys()))[0]
        for k, v in expected_values.items():
            if k in ("user_id", "recurrence_id"):
                v = (v.id, v.name) if v else False

            if isinstance(v, list):
                self.assertListEqual(
                    sorted(v), sorted(odoo_event_values.get(k)), msg=f"'{k}' mismatch"
                )
            else:
                self.assertEqual(v, odoo_event_values.get(k), msg=f"'{k}' mismatch")

    def assert_odoo_recurrence(self, odoo_recurrence, expected_values):
        """
        Assert that an Odoo recurrence has the same values than in the expected_values dictionary,
        for the keys present in expected_values.
        """
        odoo_recurrence_values = odoo_recurrence.read(list(expected_values.keys()))[0]

        for k, v in expected_values.items():
            self.assertEqual(v, odoo_recurrence_values.get(k), msg=f"'{k}' mismatch")

    def assert_dict_equal(self, dict1, dict2):
        # check missing keys
        keys = set(dict1.keys()) ^ set(dict2.keys())
        self.assertFalse(
            keys, msg="Following keys are not in both dicts: %s" % ", ".join(keys)
        )

        # compare key by key
        for k, v in dict1.items():
            self.assertEqual(v, dict2.get(k), f"'{k}' mismatch")

    def test_successful_connection(self):
        nextcloud_caldav_obj = self.env["nextcloud.caldav"]
        url = "https://next-iscale.onestein.eu"
        username = "Anjeel5"
        password = "anjeel@123"
        with recorder.use_cassette("nextcloud_connection"):
            client, principal = nextcloud_caldav_obj.check_nextcloud_connection(
                url + "/remote.php/dav", username, password
            )
            user_data = self.env["nextcloud.base"].get_user(
                principal.client.username, url, username, password
            )
            self.get_user_calendars(principal)
