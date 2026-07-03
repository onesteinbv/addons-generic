# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools.translate import LazyTranslate

_lt = LazyTranslate(__name__)


class Website(models.Model):
    _inherit = "website"

    allow_membership_registration = fields.Boolean(default=True)

    cleanup_unverified_members_days = fields.Integer(
        string="Cleanup unverified members after (days)", default=7
    )

    membership_job_id = fields.Many2one("hr.job")

    membership_registration_page_membership_group_style = fields.Selection(
        [
            ("list", "List View"),
            ("grid", "Grid View"),
        ],
        string="Membership Group View",
        default="list",
    )

    allow_adding_bio_for_membership_registration = fields.Boolean(default=False)

    membership_registration_max_cv_file_size = fields.Integer(default=3)

    membership_registration_cv_file_formats_supported = fields.Char(default=".pdf")

    def _get_checkout_step_list(self):
        steps = super()._get_checkout_step_list()
        if not self.account_on_checkout == "mandatory":
            order = self.sale_get_order()
            if order:
                if (
                    order.order_line
                    and order.order_line.mapped("product_id").filtered(
                        lambda p: p.membership
                    )
                    and self.env.user._is_public()
                ):
                    for step in steps:
                        if "website_sale.cart" in step[0]:
                            step[1]["main_button"] = _lt("Sign In")
                            step[1]["main_button_href"] = (
                                "/web/login?redirect=/shop/checkout?try_skip_step=true"
                            )
        return steps
