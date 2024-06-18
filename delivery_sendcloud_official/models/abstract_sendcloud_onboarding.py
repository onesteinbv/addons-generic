# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from odoo import api, fields, models


class SendcloudOnboardingMixin(models.AbstractModel):
    _name = "sendcloud.onboarding.mixin"
    _description = "Sendcloud Onboarding Mixin Abstract"

    sendcloud_onboarding_state = fields.Selection(
        [
            ("not_done", "Not done"),
            ("just_done", "Just done"),
            ("done", "Done"),
            ("closed", "Closed"),
        ],
        string="State of the Sendcloud onboarding panel",
        default="not_done",
    )
    sendcloud_onboarding_integration_state = fields.Selection(
        [("not_done", "Not done"), ("just_done", "Just done"), ("done", "Done")],
        string="State of the configuration integration step",
        default="not_done",
    )
    sendcloud_onboarding_sync_state = fields.Selection(
        [("not_done", "Not done"), ("just_done", "Just done"), ("done", "Done")],
        string="State of the configuration sync step",
        default="not_done",
    )
    sendcloud_onboarding_warehouse_address_state = fields.Selection(
        [("not_done", "Not done"), ("just_done", "Just done"), ("done", "Done")],
        string="State of the configuration warehouse address step",
        default="not_done",
    )

    @api.model
    def action_close_sendcloud_onboarding(self):
        """Mark the onboarding panel as closed."""
        self.env.company.sendcloud_onboarding_state = "closed"

    def get_and_update_sendcloud_onboarding_state(self):
        """This method is called on the controller rendering method and ensures that
        the animations are displayed only one time."""
        steps = self._sendcloud_onboarding_state_steps()
        return self._get_and_update_onboarding_state(
            "sendcloud_onboarding_state", steps
        )

    def _sendcloud_onboarding_state_steps(self):
        return [
            "sendcloud_onboarding_integration_state",
            "sendcloud_onboarding_sync_state",
            "sendcloud_onboarding_warehouse_address_state",
        ]

    @api.model
    def action_open_sendcloud_onboarding_integration(self):
        """Called by onboarding panel."""
        action_name = (
            "delivery_sendcloud_official.action_sendcloud_onboarding_integration_wizard"
        )
        return self.env.ref(action_name).read()[0]

    @api.model
    def action_sendcloud_onboarding_sync(self):
        """Called by onboarding panel."""
        action_name = (
            "delivery_sendcloud_official.action_sendcloud_onboarding_sync_wizard"
        )
        return self.env.ref(action_name).read()[0]

    @api.model
    def action_open_sendcloud_onboarding_warehouse_address(self):
        """Called by onboarding panel."""
        action_name = (
            "delivery_sendcloud_official.action_sendcloud_onboarding_warehouse_wizard"
        )
        return self.env.ref(action_name).read()[0]
