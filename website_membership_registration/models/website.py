# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    allow_membership_registration = fields.Boolean(default=False)

    cleanup_unverified_members_days = fields.Integer(
        string="Cleanup unverified members after (days)", default=7
    )

    membership_registration_page_background_type = fields.Selection(
        [
            ("color", "Color"),
            ("gradient_linear", "Linear-Gradient"),
            ("gradient_radial", "Radial-Gradient"),
            ("image", "Image"),
        ],
        string="Background Type",
    )

    membership_registration_page_background_color = fields.Char(string="Color")
    membership_registration_page_background_gradient_start = fields.Char(
        string="Gradient Color Start"
    )
    membership_registration_page_background_gradient_end = fields.Char(
        string="Gradient Color End"
    )

    membership_registration_page_background_image = fields.Binary()

    membership_job_id = fields.Many2one("hr.job")

    membership_registration_page_section_style = fields.Selection(
        [
            ("list", "List View"),
            ("grid", "Grid View"),
        ],
        string="Section View",
        default="list",
    )
