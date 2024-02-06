from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    committee_membership_ids = fields.One2many(
        "membership.committee.membership", "partner_id"
    )
    committee_ids = fields.Many2many(
        "membership.committee",
        string="Committees",
        compute="_compute_committee_ids",
        store=True,
    )
    committee_ids_count = fields.Integer(
        string="# of Committees", compute="_compute_committee_ids", store=True
    )

    @api.depends("committee_membership_ids", "committee_membership_ids.committee_id")
    def _compute_committee_ids(self):
        for partner in self:
            partner.committee_ids = partner.committee_membership_ids.mapped(
                "committee_id"
            )
            partner.committee_ids_count = len(partner.committee_ids)

    def action_open_committee_view(self):
        action_name = "membership_committee.membership_committee_action"
        action_vals = self.env["ir.actions.act_window"]._for_xml_id(action_name)

        action_vals["context"] = {}
        record_ids = sum([record.committee_ids.ids for record in self], [])
        # choose the view_mode accordingly
        if len(record_ids) > 1:
            # If more than 1 record was found, open the default view set on the action (usually tree, kanban or another aggregated view)
            action_vals["domain"] = (
                "[('id','in',[" + ",".join(map(str, record_ids)) + "])]"
            )
        elif len(record_ids) == 1:
            # If only 1 record was found, then open it directly on form view (aggregated views are probably not useful here)
            res = self.env.ref(
                "membership_committee.membership_committee_view_form", False
            )
            action_vals["views"] = [(res and res.id or False, "form")]
            action_vals["res_id"] = (record_ids and record_ids[0]) or False
        return action_vals
