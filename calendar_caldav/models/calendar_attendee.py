import re

from icalendar.prop import vCalAddress

from odoo import api, models


class CalendarAttendee(models.Model):
    _inherit = "calendar.attendee"

    @api.model
    def caldav_to_odoo(self, attendee):
        caldav_to_odoo_map = {
            "NEEDS-ACTION": "needsAction",
            "ACCEPTED": "accepted",
            "DECLINED": "declined",
            "TENTATIVE": "tentative",
        }
        partstat = attendee.params.get("PARTSTAT")
        state = "tentative"
        if partstat and partstat in caldav_to_odoo_map:
            state = caldav_to_odoo_map[partstat]

        match = re.search("^(mailto|MAILTO):(.*)$", attendee)
        if not match:
            raise Exception(
                "Regex for attendee failed to find an email address (%s)" % attendee
            )
        email = match.group(2)
        partner = self.env["res.partner"].search([("email", "=", email)], limit=1)
        if not partner:
            raise Exception("Partner with email `%s` doesn't exists" % email)

        return {"partner_id": partner.id, "state": state}

    def to_caldav(self):
        odoo_to_caldav_map = {
            "needsAction": "NEEDS-ACTION",
            "accepted": "ACCEPTED",
            "declined": "DECLINED",
            "tentative": "TENTATIVE",
        }
        attendees = []
        for attendee in self:
            address = vCalAddress("mailto:%s" % attendee.partner_id.email)
            address.params["CN"] = attendee.partner_id.display_name
            address.params["PARTSTAT"] = odoo_to_caldav_map[attendee.state]
            attendees.append(address)
        return attendees

    def do_tentative(self):
        res = super().do_tentative()
        self.with_delay().write_caldav()
        return res

    def do_accept(self):
        res = super().do_accept()
        self.with_delay().write_caldav()
        return res

    def do_decline(self):
        res = super().do_decline()
        self.with_delay().write_caldav()
        return res

    def write_caldav(self):
        for attendee in self.filtered(
            lambda a: a.event_id.caldav_calendar_id and a.event_id.caldav_url
        ):
            attendee.event_id.write_caldav()
