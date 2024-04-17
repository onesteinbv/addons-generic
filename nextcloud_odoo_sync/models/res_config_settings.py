# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    log_capacity = fields.Integer(
        string="Log Capacity",
        default=7,
        config_parameter="nextcloud_odoo_sync.log_capacity",
    )
    monthly_recurring_events_limit = fields.Integer(
        string="Monthly Recurring Events Limit",
        default=2,
        config_parameter="nextcloud_odoo_sync.monthly_recurring_events_limit",
    )
    daily_recurring_events_limit = fields.Integer(
        string="Daily Recurring Events Limit",
        default=2,
        config_parameter="nextcloud_odoo_sync.daily_recurring_events_limit",
    )
    weekly_recurring_events_limit = fields.Integer(
        string="Weekly Recurring Events Limit",
        default=2,
        config_parameter="nextcloud_odoo_sync.weekly_recurring_events_limit",
    )
    yearly_recurring_events_limit = fields.Integer(
        string="Yearly Recurring Events Limit",
        default=10,
        config_parameter="nextcloud_odoo_sync.yearly_recurring_events_limit",
    )
