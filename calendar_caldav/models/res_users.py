from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    caldav_url = fields.Char()
    caldav_username = fields.Char()
    caldav_password = fields.Char()
    caldav_email = fields.Char(
        help="In some systems the username you use to authenticate is different "
        "from the email address (organizer) in the calendar"
    )

    default_caldav_calendar_id = fields.Many2one(comodel_name="calendar.caldav")

    def action_caldav_calendar_sync(self):
        self.ensure_one()
        action = (
            self.env.ref("calendar_caldav.calendar_caldav_sync_wizard_action")
            .sudo()
            .read()[0]
        )
        return action
