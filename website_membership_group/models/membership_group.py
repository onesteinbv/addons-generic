# Copyright 2020 Onestein (<https://www.onestein.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.translate import html_translate


class MembershipGroup(models.Model):
    _name = "membership.group"
    _inherit = ["membership.group", "website.published.mixin", "website.seo.metadata"]

    website_top = fields.Html(strip_style=True, translate=html_translate)
    website_bottom = fields.Html(strip_style=True, translate=html_translate)
    image = fields.Image()
    icon = fields.Image()
    page_id = fields.Many2one(comodel_name="website.page")
    website_url = fields.Char(compute="_compute_website_url", store=True)
    website_snippet_wrap_classes = fields.Char(
        string="Wrap Classes",
        default="mg_show_image mg_show_top mg_show_bottom mg_show_committee mg_show_team",
        help="Classes for the #wrap element (visibility options)",
    )
    website_snippet_members_classes = fields.Char(
        string="Members Row Classes",
        default="mg_layout_grid mg_show_committee_desc mg_show_team_desc",
        help="Classes for the #mg_members_row element (layout and description options)",
    )
    website_committee_col_classes = fields.Char(
        string="Committee Column Classes", default="col-lg-4"
    )
    website_team_col_classes = fields.Char(
        string="Team Column Classes", default="col-lg-8"
    )

    @api.depends("page_id", "page_id.is_published")
    def _compute_website_url(self):
        slug = self.env["ir.http"]._slug
        for membership_group in self:
            membership_group.website_url = (
                membership_group.page_id
                and membership_group.page_id.is_published
                and membership_group.page_id.url
                or "/members/group/%s" % slug(membership_group)
            )

    def _create_membership_page(self):
        """Create a unique website.page for this membership group."""
        self.ensure_one()
        if self.page_id:
            return self.page_id

        slug = self.env["ir.http"]._slug
        page_url = "/members/group/%s" % slug(self)
        view_key = "website_membership_group.membership_group_page_custom_%s" % self.id

        # Create the view with unique oe_structure IDs
        view = self.env["ir.ui.view"].create({
            "name": "Membership Group: %s" % self.name,
            "key": view_key,
            "type": "qweb",
            "arch": self._get_page_arch(),
        })

        # Create the website page
        page = self.env["website.page"].create({
            "url": page_url,
            "website_published": True,
            "view_id": view.id,
        })

        self.page_id = page
        return page

    def _get_page_arch(self):
        """Return the raw QWeb arch from the base template."""
        view = self.env.ref("website_membership_group.membership_group_page_base")
        return view.arch

    def write(self, vals):
        """Auto-create page on publish, sync publish status on both transitions."""
        res = super().write(vals)
        if "is_published" in vals:
            for group in self:
                if group.is_published and not group.page_id:
                    group._create_membership_page()
                if group.page_id and group.page_id.is_published != group.is_published:
                    group.page_id.is_published = group.is_published
        return res