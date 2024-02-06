from caldav import DAVClient

from odoo import api, fields, models


class CalendarCalDAV(models.Model):
    _name = "calendar.caldav"
    _description = "CalDAV Calendar"

    user_id = fields.Many2one(
        comodel_name="res.users", required=True, ondelete="cascade"
    )
    url = fields.Char()
    name = fields.Char()
    enabled = fields.Boolean()

    def get_caldav_object(self):
        self.ensure_one()
        client = DAVClient(
            url=self.user_id.caldav_url,
            username=self.user_id.caldav_username,
            password=self.user_id.caldav_password,
        )
        principal = client.principal()
        return principal.calendar(cal_url=self.url)

    def import_caldav_events(self):
        for calendar in self.filtered(lambda c: c.enabled):
            self.env["calendar.event"].with_delay().import_caldav_events(calendar)

    @api.model
    def cron_import_caldav_events(self):
        calendars = self.search([("enabled", "=", True)])
        for calendar in calendars:
            last_event = self.env["calendar.event"].search(
                [("caldav_calendar_id", "=", calendar.id)],
                order="caldav_dtstamp desc",
                limit=1,
            )
            self.env["calendar.event"].with_delay().import_caldav_events(
                calendar, date_from=last_event.caldav_dtstamp
            )
            self.env["calendar.event"].with_delay().cleanup_caldav_events(calendar)
