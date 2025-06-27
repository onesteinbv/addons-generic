from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    membership_group_member_ids = fields.One2many(
        "membership.group.member",
        "partner_id",
    )
    membership_group_ids = fields.Many2many(
        "membership.group",
        string="Membership Groups",
        compute="_compute_membership_group_ids",
        store=True,
    )
    membership_group_ids_count = fields.Integer(
        string="# of Groups",
        compute="_compute_membership_group_ids",
        store=True,
    )
    member_can_vote = fields.Boolean(
        compute="_compute_member_can_vote",
        store=True,
        string="Can Vote",
    )

    @api.depends(
        "membership_group_member_ids",
        "membership_group_member_ids.group_id",
        "membership_group_member_ids.state",
    )
    def _compute_membership_group_ids(self):
        for partner in self:
            partner.membership_group_ids = partner.membership_group_member_ids.filtered(
                lambda x: x.state == "current"
            ).mapped("group_id")
            partner.membership_group_ids_count = len(partner.membership_group_ids)

    @api.depends("membership_group_ids", "membership_group_ids.voting_group")
    def _compute_member_can_vote(self):
        for partner in self:
            partner.member_can_vote = bool(
                partner.membership_group_ids.filtered("voting_group")
            )

    def action_open_membership_group_view(self):
        action_name = "membership_group.membership_group_action"
        action_vals = self.env["ir.actions.act_window"]._for_xml_id(action_name)

        action_vals["context"] = {}
        record_ids = self.mapped("membership_group_ids").ids
        # choose the view_mode accordingly
        if len(record_ids) > 1:
            action_vals["domain"] = (
                "[('id','in',[" + ",".join(map(str, record_ids)) + "])]"
            )
        elif len(record_ids) == 1:
            res = self.env.ref("membership_group.membership_group_view_form", False)
            action_vals["views"] = [(res and res.id or False, "form")]
            action_vals["res_id"] = record_ids[0]
        return action_vals
