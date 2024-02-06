from urllib import parse

import requests
from requests.auth import HTTPBasicAuth

from odoo import _, fields, models
from odoo.exceptions import UserError


class CalendarCaldavSyncWizard(models.TransientModel):
    _inherit = "calendar.caldav.sync.wizard"

    nextcloud = fields.Boolean(
        string="Is Nextcloud", default=lambda self: self.env.user.caldav_nextcloud
    )

    def _get_caldav_email(self):
        self.ensure_one()
        if self.nextcloud:
            email = self._nextcloud_request_email()
            if not email:
                raise UserError(
                    _(
                        "There's no primary email address configured. "
                        "Please configure a primary email address in Nextcloud and try again."
                    )
                )
            return email
        return super()._get_caldav_email()

    def _nextcloud_request_email(self):
        self.ensure_one()
        parsed_url = parse.urlparse(self.url)
        base_url = "%s://%s" % (parsed_url.scheme, parsed_url.netloc)
        response = requests.get(
            url="%s/ocs/v2.php/cloud/user?format=json" % base_url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={"OCS-APIRequest": "true"},
        )
        json = response.json()
        return json["ocs"]["data"]["email"]

    def _autocomplete_caldav_url(self):
        self.ensure_one()
        if self.nextcloud and not self.url.endswith("remote.php/dav"):
            return parse.urljoin(self.url, "remote.php/dav")
        return super()._autocomplete_caldav_url()

    def _prepare_user_values(self):
        vals = super()._prepare_user_values()
        vals["caldav_nextcloud"] = self.nextcloud
        return vals
