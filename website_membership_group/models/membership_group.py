# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.translate import html_translate

from odoo.addons.http_routing.models.ir_http import slug


class MembershipGroup(models.Model):
    _name = "membership.group"
    _inherit = ["membership.group", "website.published.mixin"]

    website_top = fields.Html(strip_style=True, translate=html_translate)
    website_bottom = fields.Html(strip_style=True, translate=html_translate)
    image = fields.Image()
    icon = fields.Image()
    page_id = fields.Many2one(comodel_name="website.page")
    website_url = fields.Char(compute="_compute_website_url", store=True)

    @api.depends("page_id", "page_id.is_published")
    def _compute_website_url(self):
        for membership_group in self:
            membership_group.website_url = (
                membership_group.page_id
                and membership_group.page_id.is_published
                and membership_group.page_id.url
                or "/members/group/%s" % slug(membership_group)
            )
