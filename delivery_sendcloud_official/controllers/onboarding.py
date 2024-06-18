# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from odoo import http
from odoo.http import request


class OnboardingController(http.Controller):
    @http.route("/sendcloud/sendcloud_onboarding_panel", auth="user", type="json")
    def sendcloud_onboarding(self):
        """Returns the `banner` for the Sendcloud onboarding panel.
        It can be empty if the user has closed it or if he doesn't have
        the permission to see it."""

        company = request.env.company
        if not request.env.is_admin() or company.sendcloud_onboarding_state == "closed":
            return {}

        panel_name = self._sendcloud_onboarding_panel_name()
        return {
            "html": request.env["ir.qweb"]._render(
                panel_name,
                {
                    "company": company,
                    "state": company.get_and_update_sendcloud_onboarding_state(),
                },
            )
        }

    def _sendcloud_onboarding_panel_name(self):
        return "delivery_sendcloud_official.sendcloud_onboarding_panel"
