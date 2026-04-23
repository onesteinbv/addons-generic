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
        """Return the page architecture with unique IDs for this group."""
        return """<t t-call="website.layout">
            <t t-set="additional_title" t-value="membership_group.name"/>
            <div id="wrap"
                 t-att-data-oe-id="membership_group.id"
                 t-attf-class="mg_wrap o_editable {{membership_group.website_snippet_wrap_classes or 'mg_show_image mg_show_top mg_show_bottom mg_show_committee mg_show_team'}}">
                <div class="oe_structure" id="oe_structure_mg_%s_1"/>
                <section class="mg_header_section pt-5 pb-4">
                    <div class="container" name="membership_page">
                        <div class="row" name="description_row">
                            <div class="col-12 text-center mb-4">
                                <h2 class="fw-bold text-primary" t-field="membership_group.name"/>
                                <hr class="w-25 mx-auto mt-2 mb-0 mg_divider opacity-50"/>
                            </div>
                        </div>
                        <div class="row align-items-start g-4">
                            <div class="col-lg-4 text-center mg_image_col">
                                <div t-field="membership_group.image"
                                     t-options='{"widget": "image", "class": "img-fluid rounded shadow"}'/>
                            </div>
                            <div class="col-lg-8 mg_desc_col">
                                <div class="mg_top_block" t-field="membership_group.website_top"/>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="mg_members_section py-5">
                    <div class="container">
                        <div class="oe_structure" id="oe_structure_mg_%s_2"/>
                        <div t-attf-class="row g-4 mg_members_row {{membership_group.website_snippet_members_classes or 'mg_layout_grid mg_show_committee_desc mg_show_team_desc'}}"
                             id="mg_members_row"
                             t-att-data-oe-id="membership_group.id"
                        >
                            <t t-set="current_members"
                                               t-value="membership_group.membership_group_member_ids.filtered(lambda m: m.state == 'current')"/>
                            <div t-attf-class="mg_committee_col {{membership_group.website_committee_col_classes or 'col-lg-4'}}">
                                <div class="card h-100 shadow-sm border-0">
                                    <div class="card-header border-0 py-3 bg-primary text-white"
                                         data-name="Committee Header">
                                        <h5 class="mb-0 fw-semibold">Committee Members</h5>
                                    </div>
                                    <div class="card-body p-0">
                                        <div>
                                            <t t-set="committee_members"
                                               t-value="current_members.filtered(lambda m: m.type == 'committee').mapped('partner_id')"/>
                                            <t t-call="website_membership_group.membership_group_member_list">
                                                <t t-set="members" t-value="committee_members"/>
                                            </t>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div t-attf-class="mg_team_col {{membership_group.website_team_col_classes or 'col-lg-8'}}">
                                <div class="card h-100 shadow-sm border-0">
                                    <div class="card-header border-0 py-3 bg-primary text-white"
                                         data-name="Team Header">
                                        <h5 class="mb-0 fw-semibold">Team Members</h5>
                                    </div>
                                    <div class="card-body p-0">
                                        <div>
                                            <t t-set="team_members"
                                               t-value="current_members.filtered(lambda m: m.type != 'committee').mapped('partner_id')"/>
                                            <t t-call="website_membership_group.membership_group_member_list">
                                                <t t-set="members" t-value="team_members"/>
                                            </t>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="oe_structure" id="oe_structure_mg_%s_3"/>
                    </div>
                </section>
                <section class="mg_bottom_block pt-3">
                    <div class="container">
                        <div class="row">
                            <div class="mt-3" t-field="membership_group.website_bottom"/>
                        </div>
                    </div>
                </section>
                <div class="oe_structure" id="oe_structure_mg_%s_4"/>
            </div>
        </t>""" % (self.id, self.id, self.id, self.id)

    def write(self, vals):
        """Auto-create page when published."""
        res = super().write(vals)
        if vals.get("is_published"):
            for group in self:
                if not group.page_id:
                    group._create_membership_page()
        return res