# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    allow_membership_registration = fields.Boolean(default=False)

    cleanup_unverified_members_days = fields.Integer(
        string="Cleanup unverified members after (days)", default=7
    )

    membership_job_id = fields.Many2one("hr.job")

    membership_registration_page_section_style = fields.Selection(
        [
            ("list", "List View"),
            ("grid", "Grid View"),
        ],
        string="Section View",
        default="list",
    )

    allow_adding_bio_for_membership_registration = fields.Boolean(default=False)

    membership_registration_max_cv_file_size = fields.Integer(default=3)

    membership_registration_cv_file_formats_supported = fields.Char(default=".pdf")
