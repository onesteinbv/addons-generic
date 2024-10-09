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

    membership_registration_page_section_style = fields.Selection(
        related="website_id.membership_registration_page_section_style",
        readonly=False,
    )

    membership_registration_max_cv_file_size = fields.Integer(
        related="website_id.membership_registration_max_cv_file_size",
        readonly=False,
    )

    membership_registration_cv_file_formats_supported = fields.Char(
        related="website_id.membership_registration_cv_file_formats_supported",
        readonly=False,
    )
