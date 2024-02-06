# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    allow_membership_registration = fields.Boolean(
        related="website_id.allow_membership_registration",
        readonly=False,
    )

    cleanup_unverified_members_days = fields.Integer(
        related="website_id.cleanup_unverified_members_days",
        readonly=False,
    )

    membership_job_id = fields.Many2one(
        related="website_id.membership_job_id",
        readonly=False,
    )

    membership_registration_page_background_type = fields.Selection(
        related="website_id.membership_registration_page_background_type",
        readonly=False,
        string="Background Type",
    )

    membership_registration_page_background_color = fields.Char(
        related="website_id.membership_registration_page_background_color",
        readonly=False,
        string="Color",
    )
    membership_registration_page_background_gradient_start = fields.Char(
        related="website_id.membership_registration_page_background_gradient_start",
        readonly=False,
        string="Gradient Color Start",
    )
    membership_registration_page_background_gradient_end = fields.Char(
        related="website_id.membership_registration_page_background_gradient_end",
        readonly=False,
        string="Gradient Color End",
    )

    membership_registration_page_background_image = fields.Binary(
        related="website_id.membership_registration_page_background_image",
        readonly=False,
    )

    membership_registration_page_section_style = fields.Selection(
        related="website_id.membership_registration_page_section_style",
        readonly=False,
    )
