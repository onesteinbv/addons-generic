from odoo import api, fields, models


class MembershipSection(models.Model):
    _inherit = "membership.section"

    committee_id = fields.Many2one(
        "membership.committee",
        compute="_compute_committee",
        inverse="_inverse_committee",
        store=True,
        readonly=False,
    )

    committee_ids = fields.One2many(
        "membership.committee", "section_id", string="Committees"
    )

    @api.depends("committee_ids")
    def _compute_committee(self):
        for section in self:
            if len(self.committee_ids) > 0:
                section.committee_id = section.committee_ids[0]
            else:
                section.committee_id = False

    def _inverse_committee(self):
        for section in self:
            if len(section.committee_ids) > 0:
                committee = self.env["membership.committee"].browse(
                    section.committee_ids[0].id
                )
                committee.section_id = False
            section.committee_id.section_id = section
