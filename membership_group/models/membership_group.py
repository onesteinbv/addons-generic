from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MembershipGroup(models.Model):
    _name = "membership.group"
    _description = "Membership Group"
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = "complete_name"
    _order = "complete_name"

    name = fields.Char()
    complete_name = fields.Char(
        compute="_compute_complete_name", recursive=True, store=True
    )
    membership_group_member_ids = fields.One2many(
        "membership.group.member",
        "group_id",
    )
    parent_id = fields.Many2one(
        comodel_name="membership.group", string="Parent", index=True
    )
    child_ids = fields.One2many(
        comodel_name="membership.group",
        inverse_name="parent_id",
        string="Subgroups",
    )
    parent_path = fields.Char(index=True)
    partner_ids = fields.Many2many(
        "res.partner",
        string="Contacts",
        compute="_compute_partner_ids",
        store=True,
        compute_sudo=False,
    )
    partner_ids_count = fields.Integer(
        "# of Members", compute="_compute_partner_ids", store=True, compute_sudo=False
    )

    membership_end_date = fields.Date(
        help="Default date to for members of this group",
    )
    voting_group = fields.Boolean(copy=False)

    @api.constrains("voting_group")
    def _check_voting_group(self):
        """Only allow one voting group"""
        if voting_groups := self.search([("voting_group", "=", True)]):
            if not voting_groups or len(voting_groups) == 1:
                return
            raise ValidationError(self.env._("Only one voting group is allowed"))

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for group in self:
            if group.parent_id:
                group.complete_name = f"{group.parent_id.complete_name} / {group.name}"
            else:
                group.complete_name = group.name

    @api.depends(
        "membership_group_member_ids",
        "membership_group_member_ids.partner_id",
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
