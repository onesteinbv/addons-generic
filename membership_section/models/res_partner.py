from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    section_membership_ids = fields.One2many(
        "membership.section.membership", "partner_id"
    )
    section_ids = fields.Many2many(
        "membership.section",
        string="Membership Sections",
        compute="_compute_section_ids",
        store=True,
    )
    section_ids_count = fields.Integer(
        string="# of Sections", compute="_compute_section_ids", store=True
    )

    @api.depends("section_membership_ids", "section_membership_ids.section_id")
    def _compute_section_ids(self):
        for partner in self:
            partner.section_ids = partner.section_membership_ids.mapped("section_id")
            partner.section_ids_count = len(partner.section_ids)

    def action_open_section_view(self):
        action_name = "membership_section.membership_section_action"
        action_vals = self.env["ir.actions.act_window"]._for_xml_id(action_name)

        action_vals["context"] = {}
        record_ids = sum((record.section_ids.ids for record in self), [])
        # choose the view_mode accordingly
        if len(record_ids) > 1:
            action_vals["domain"] = (
                "[('id','in',[" + ",".join(map(str, record_ids)) + "])]"
            )
        elif len(record_ids) == 1:
            res = self.env.ref("membership_section.membership_section_view_form", False)
            action_vals["views"] = [(res and res.id or False, "form")]
            action_vals["res_id"] = (record_ids and record_ids[0]) or False
        return action_vals
