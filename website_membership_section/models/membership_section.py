# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.translate import html_translate

from odoo.addons.http_routing.models.ir_http import slug


class MembershipSection(models.Model):
    _name = "membership.section"
    _inherit = ["membership.section", "website.published.mixin"]

    website_top = fields.Html(strip_style=True, translate=html_translate)
    website_bottom = fields.Html(strip_style=True, translate=html_translate)
    image = fields.Image()
    icon = fields.Image()
    page_id = fields.Many2one(comodel_name="website.page")
    website_url = fields.Char(compute="_compute_website_url", store=True)

    @api.depends("page_id", "page_id.is_published")
    def _compute_website_url(self):
        for section in self:
            section.website_url = (
                section.page_id
                and section.page_id.is_published
                and section.page_id.url
                or "/members/section/%s" % slug(section)
            )
