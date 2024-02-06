from odoo import api, fields, models


class MembershipSection(models.Model):
    _name = "membership.section"
    _description = "Membership Section"

    name = fields.Char()
    section_membership_ids = fields.One2many(
        "membership.section.membership", "section_id"
    )
    partner_ids = fields.Many2many(
        "res.partner", string="Contacts", compute="_compute_partner_ids"
    )
    partner_ids_count = fields.Integer("# of Members", compute="_compute_partner_ids")

    @api.depends("section_membership_ids", "section_membership_ids.partner_id")
    def _compute_partner_ids(self):
        for section in self:
            section.partner_ids = section.section_membership_ids.mapped("partner_id")
            section.partner_ids_count = len(section.partner_ids)

    def action_open_partner_view(self):
        action_name = "membership.action_membership_members"
        action_vals = self.env["ir.actions.act_window"]._for_xml_id(action_name)

        action_vals["context"] = {}
        record_ids = sum((record.partner_ids.ids for record in self), [])
        if len(record_ids) > 1:
            action_vals["domain"] = (
                "[('id','in',[" + ",".join(map(str, record_ids)) + "])]"
            )
        elif len(record_ids) == 1:
            res = self.env.ref("base.view_partner_form", False)
            action_vals["views"] = [(res and res.id or False, "form")]
            action_vals["res_id"] = (record_ids and record_ids[0]) or False
        return action_vals
