from odoo import api, fields, models


class MembershipCommittee(models.Model):
    _name = "membership.committee"
    _description = "Committee"

    name = fields.Char(compute="_compute_name", store=True, readonly=False)
    section_id = fields.Many2one("membership.section", required=False)
    committee_membership_ids = fields.One2many(
        "membership.committee.membership", "committee_id"
    )
    partner_ids = fields.Many2many(
        "res.partner", string="Partners", compute="_compute_partner_ids"
    )
    partner_ids_count = fields.Integer("# of Members", compute="_compute_partner_ids")

    @api.depends("committee_membership_ids", "committee_membership_ids.partner_id")
    def _compute_partner_ids(self):
        for committee in self:
            committee.partner_ids = committee.committee_membership_ids.mapped(
                "partner_id"
            )
            committee.partner_ids_count = len(committee.partner_ids)

    @api.depends("section_id")
    def _compute_name(self):
        for committee in self:
            if committee.section_id:
                committee.name = committee.section_id.name
            else:
                committee.name = ""

    def action_open_partner_view(self):
        action_name = "membership.action_membership_members"
        action_vals = self.env["ir.actions.act_window"]._for_xml_id(action_name)

        action_vals["context"] = {}
        record_ids = sum([record.partner_ids.ids for record in self], [])
        # choose the view_mode accordingly
        if len(record_ids) > 1:
            # If more than 1 record was found, open the default view set on the action (usually tree, kanban or another aggregated view)
            action_vals["domain"] = (
                "[('id','in',[" + ",".join(map(str, record_ids)) + "])]"
            )
        elif len(record_ids) == 1:
            # If only 1 record was found, then open it directly on form view (aggregated views are probably not useful here)
            res = self.env.ref("base.view_partner_form", False)
            action_vals["views"] = [(res and res.id or False, "form")]
            action_vals["res_id"] = (record_ids and record_ids[0]) or False
        return action_vals
