from caldav import DAVClient
from caldav.lib.error import AuthorizationError, NotFoundError, PropfindError
from requests.exceptions import (  # pylint: disable=redefined-builtin
    ConnectionError,
    MissingSchema,
)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CalendarCaldavSyncWizard(models.TransientModel):
    _name = "calendar.caldav.sync.wizard"
    _inherit = ["multi.step.wizard.mixin"]

    user_id = fields.Many2one(
        comodel_name="res.users", default=lambda self: self.env.user, readonly=True
    )
    url = fields.Char(
        string="URL",
        help="E.g. https://zimbra.company.com/dav or https://nextcloud.company.com/remote.php/dav",
        default=lambda self: self.env.user.caldav_url,
    )
    username = fields.Char(default=lambda self: self.env.user.caldav_username)
    password = fields.Char(default=lambda self: self.env.user.caldav_password)
    calendar_ids = fields.Many2many(
        comodel_name="calendar.caldav",
        domain=lambda self: [("user_id", "=", self.env.user.id)],
        default=lambda self: self.env["calendar.caldav"].search(
            [("user_id", "=", self.env.user.id), ("enabled", "=", True)]
        ),
        string="Calendars",
    )
    default_calendar_id = fields.Many2one(
        comodel_name="calendar.caldav",
        default=lambda self: self.env.user.default_caldav_calendar_id.id,
    )

    def _reopen_self(self):
        action = super()._reopen_self()
        action["name"] = _("Synchronize CalDAV Calendar")
        return action

    @api.model
    def _selection_state(self):
        return [
            ("start", "Connect"),
            ("select", "Select Calendars"),
            ("sync", "Synchronize"),
            ("final", "Configuration Completed"),
        ]

    def _prepare_calendar_vals(self, caldav_calendar):
        self.ensure_one()
        return {
            "user_id": self.user_id.id,
            "url": caldav_calendar.canonical_url,
            "name": caldav_calendar.name,
        }

    def _sync_calendars(self):
        self.ensure_one()
        client = DAVClient(url=self.url, username=self.username, password=self.password)
        # Try to give as much user-friendly error messaging as possible.
        try:
            principal = client.principal()
        except (PropfindError, NotFoundError, ConnectionError) as e:
            raise UserError(
                _("Invalid CalDAV endpoint, please check the URL and try again\n\n %s")
                % e
            ) from e
        except MissingSchema as e:
            raise UserError(
                _("Make sure the schema is in the URL e.g. https:// or http://")
            ) from e
        except AuthorizationError as e:
            raise UserError(
                _("Your username or password seems to be incorrect\n\n %s") % e
            ) from e

        # Existing calendars
        user_calendars = self.env["calendar.caldav"].search(
            [("user_id", "=", self.user_id.id)]
        )

        # Get calendars and prepare values for `calendar.caldav` records
        calendars = principal.calendars()
        synced_calendar_urls = []
        vals_list = []
        for calendar in calendars:
            existing_calendar = user_calendars.filtered(
                lambda c: c.url == calendar.canonical_url
            )
            if existing_calendar:
                existing_calendar.write({"name": calendar.name})
            else:
                vals_list.append(self._prepare_calendar_vals(calendar))
            synced_calendar_urls.append(calendar.canonical_url)
        # Create new calendars
        self.env["calendar.caldav"].create(vals_list)
        # Remove deleted calendars
        user_calendars.filtered(lambda c: c.url not in synced_calendar_urls).unlink()

    def _get_caldav_email(self):
        self.ensure_one()
        return self.username

    def _autocomplete_caldav_url(self):
        self.ensure_one()
        return self.url

    def _prepare_user_values(self):
        self.ensure_one()
        return {
            "caldav_url": self._autocomplete_caldav_url(),
            "caldav_username": self.username,
            "caldav_password": self.password,
            "caldav_email": self._get_caldav_email(),
        }

    def state_exit_start(self):
        self.ensure_one()
        self._sync_calendars()

        # Persist connection info
        self.user_id.sudo().write(self._prepare_user_values())

        self.state = "select"

    def state_exit_select(self):
        # Enable calendars
        self.calendar_ids.write({"enabled": True})
        # Disable others
        user_calendars = self.env["calendar.caldav"].search(
            [("user_id", "=", self.user_id.id)]
        )
        (user_calendars - self.calendar_ids).write({"enabled": False})
        # Set default
        self.user_id.sudo().write(
            {"default_caldav_calendar_id": self.default_calendar_id.id}
        )
        self.state = "sync"

    def state_exit_sync(self):
        self.calendar_ids.import_caldav_events()
        self.state = "final"

    def state_previous_select(self):
        self.state = "start"

    def state_previous_sync(self):
        self.state = "select"
