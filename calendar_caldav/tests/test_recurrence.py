from odoo import fields
from odoo.tests.common import TransactionCase


class TestRecurrence(TransactionCase):
    def test_exceptions(self):
        base_event = self.env["calendar.event"].create(
            {
                "name": "/",
                "start": fields.Datetime.to_datetime("2023-09-01 12:00:00"),
                "stop": fields.Datetime.to_datetime("2023-09-01 13:00:00"),
                "recurrency": True,
                "rrule_type": "weekly",
                "end_type": "count",
                "count": 10,
                "mon": True,
                "event_tz": "Europe/Amsterdam",
                "exceptions": {
                    "dts": [
                        "2023-09-04 12:00:00",
                        "2023-09-18 12:00:00",
                        "2023-11-06 12:00:00",  # DST change test
                    ]
                },
            }
        )

        recurrence = self.env["calendar.recurrence"].search(
            [("base_event_id", "=", base_event.id)]
        )

        self.assertEqual(len(recurrence.calendar_event_ids), 7)
        self.assertFalse(
            recurrence.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-04 12:00:00")
            )
        )
        self.assertFalse(
            recurrence.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-18 12:00:00")
            )
        )
        self.assertTrue(
            recurrence.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-11 12:00:00")
            )
        )
        self.assertTrue(
            recurrence.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-11 12:00:00")
            )
        )
        self.assertFalse(
            recurrence.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-11-06 12:00:00")
            )
        )

    def test_rrule_with_exdates(self):
        base_event = self.env["calendar.event"].create(
            {
                "name": "/",
                "start": fields.Datetime.to_datetime("2023-09-01 12:00:00"),
                "stop": fields.Datetime.to_datetime("2023-09-01 13:00:00"),
                "recurrency": True,
                "rrule_type": "weekly",
                "end_type": "count",
                "count": 10,
                "mon": True,
                "event_tz": "Europe/Amsterdam",
                "exceptions": {
                    "dts": [
                        "2023-09-04 12:00:00",
                        "2023-09-18 12:00:00",
                        "2023-11-06 12:00:00",  # DST change test
                    ]
                },
            }
        )

        recurrence = self.env["calendar.recurrence"].search(
            [("base_event_id", "=", base_event.id)]
        )
        self.assertEqual(len(recurrence.calendar_event_ids), 7)

        event_test = self.env["calendar.event"].create(
            {
                "name": "/",
                "start": fields.Datetime.to_datetime("2023-09-01 12:00:00"),
                "stop": fields.Datetime.to_datetime("2023-09-01 13:00:00"),
                "recurrency": True,
                "event_tz": "Europe/Amsterdam",
                "rrule": recurrence.rrule,
            }
        )
        recurrence_test = self.env["calendar.recurrence"].search(
            [("base_event_id", "=", event_test.id)]
        )

        self.assertEqual(recurrence_test.rrule_type, "weekly")
        self.assertEqual(recurrence_test.count, 10)
        self.assertTrue(recurrence_test.mon)
        self.assertIn("2023-09-04 12:00:00", recurrence_test.exceptions["dts"])
        self.assertIn("2023-09-18 12:00:00", recurrence_test.exceptions["dts"])
        self.assertIn("2023-11-06 12:00:00", recurrence_test.exceptions["dts"])
        self.assertEqual(len(recurrence_test.calendar_event_ids), 7)
        self.assertFalse(
            recurrence_test.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-04 12:00:00")
            )
        )
        self.assertFalse(
            recurrence_test.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-18 12:00:00")
            )
        )
        self.assertTrue(
            recurrence_test.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-11 12:00:00")
            )
        )
        self.assertTrue(
            recurrence_test.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-09-11 12:00:00")
            )
        )
        self.assertFalse(
            recurrence_test.calendar_event_ids.filtered(
                lambda c: c.start == fields.Datetime.to_datetime("2023-11-06 12:00:00")
            )
        )

    def test_rrule_to_caldav(self):
        base_event = self.env["calendar.event"].create(
            {
                "name": "/",
                "start": fields.Datetime.to_datetime("2023-09-01 12:00:00"),
                "stop": fields.Datetime.to_datetime("2023-09-01 13:00:00"),
                "recurrency": True,
                "rrule_type": "weekly",
                "end_type": "count",
                "count": 10,
                "mon": True,
                "event_tz": "Europe/Amsterdam",
                "exceptions": {
                    "dts": [
                        "2023-09-04 12:00:00",
                        "2023-09-18 12:00:00",
                        "2023-11-06 12:00:00",  # DST change test
                    ]
                },
            }
        )
        recurrence = self.env["calendar.recurrence"].search(
            [("base_event_id", "=", base_event.id)]
        )

        recurrence.to_caldav()
