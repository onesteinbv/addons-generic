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
    page_id = fields.Many2one(
        comodel_name="website.page", string="Website Page", ondelete="set null"
    )
    website_url = fields.Char(compute="_compute_website_url", store=True)
    website_snippet_wrap_classes = fields.Char(
        string="Wrap Classes",
        default="mg_wrap mg_show_image mg_show_top mg_show_bottom mg_show_committee mg_show_team",
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
    website_header_image_col_classes = fields.Char(
        string="Website Header Image Column Classes", default="col-lg-4"
    )
    website_header_desc_col_classes = fields.Char(
        string="Website Header Description Column Classes", default="col-lg-8"
    )

    _sql_constraints = [
        (
            "page_id_unique",
            "unique(page_id)",
            "A website page can only be assigned to one unique Membership Group!",
        )
    ]

    @api.depends("page_id", "page_id.url")
    def _compute_website_url(self):
        slug = self.env["ir.http"]._slug
        for membership_group in self:
            membership_group.website_url = (
                membership_group.page_id
                and membership_group.page_id.url
                or "/members/group/%s" % slug(membership_group)
            )

    @api.model_create_multi
    def create(self, vals_list):
        groups = super(MembershipGroup, self).create(vals_list)
        for group in groups:
            if group.page_id and group.page_id.is_published != group.is_published:
                group.page_id.sudo().write({"is_published": group.is_published})
        return groups

    def write(self, vals):
        res = super(MembershipGroup, self).write(vals)
        if "is_published" in vals or "page_id" in vals:
            for group in self:
                if group.page_id and group.page_id.is_published != group.is_published:
                    group.page_id.sudo().write({"is_published": group.is_published})
        return res

    def _create_unique_website_page(self):
        """Generates a dedicated website.page for this group cloned from the base template."""
        self.ensure_one()
        if self.page_id:
            return self.page_id

        website = self.env["website"].get_current_website()
        slug = self.env["ir.http"]._slug(self)
        page_url = f"/members/group/{slug}"

        existing_page = self.env["website.page"].search(
            [("url", "=", page_url), ("website_id", "=", website.id)], limit=1
        )

        if existing_page:
            self.write({"page_id": existing_page.id})
            return existing_page
        base_view = self.env.ref("website_membership_group.membership_group_page")
        new_view = base_view.copy(
            {
                "name": f"Membership Group Page: {self.name}",
                "key": f"website_membership_group.membership_group_page_{self.id}",
                "type": "qweb",
                "website_id": website.id,
            }
        )
        page = self.env["website.page"].create(
            {
                "view_id": new_view.id,
                "url": page_url,
                "is_published": self.is_published,
                "website_id": website.id,
            }
        )

        self.write({"page_id": page.id})
        return page
