from odoo import api, fields, models


class MembershipGroup(models.Model):
    _name = "membership.group"
    _description = "Membership Group"
    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char()
    membership_group_member_ids = fields.One2many("membership.group.member", "group_id")
    parent_id = fields.Many2one(
        comodel_name="membership.group", string="Parent Membership Group", index=True
    )
    child_ids = fields.One2many(
        comodel_name="membership.group",
        inverse_name="parent_id",
        string="Sub Membership Groups",
    )
    parent_path = fields.Char(index=True, unaccent=False)
    partner_ids = fields.Many2many(
        "res.partner", string="Contacts", compute="_compute_partner_ids"
    )
    partner_ids_count = fields.Integer("# of Members", compute="_compute_partner_ids")

    @api.depends(
        "membership_group_member_ids", "membership_group_member_ids.partner_id"
    )
    def _compute_partner_ids(self):
        for group in self:
            group.partner_ids = group.membership_group_member_ids.mapped("partner_id")
            group.partner_ids_count = len(group.partner_ids)

    def action_open_partner_view(self):
        action_name = "membership.action_membership_members"
        action_vals = self.env["ir.actions.act_window"]._for_xml_id(action_name)
        action_vals["context"] = {}
        record_ids = self.mapped("partner_ids").ids
        if len(record_ids) > 1:
            action_vals["domain"] = (
                "[('id','in',[" + ",".join(map(str, record_ids)) + "])]"
            )
        elif len(record_ids) == 1:
            res = self.env.ref("base.view_partner_form", False)
            action_vals["views"] = [(res and res.id or False, "form")]
            action_vals["res_id"] = record_ids[0]
        return action_vals
