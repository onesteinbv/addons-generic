from odoo import api, fields, models


class MembershipGroupMember(models.Model):
    _inherit = "membership.group.member"

    on_mailing_list = fields.Boolean(
        compute="_compute_on_mailing_list",
        inverse="_inverse_on_mailing_list",
        store=True,
        readonly=False,
    )

    @api.depends(
        "group_id",
        "group_id.mailing_list_id",
        "partner_id",
        "partner_id.mass_mailing_contact_ids",
    )
    def _compute_on_mailing_list(self):
        for membership in self:
            if (
                not membership.group_id
                or not membership.group_id.mailing_list_id
                or not membership.partner_id
            ):
                membership.on_mailing_list = False
            else:
                related_lists = membership.partner_id.mass_mailing_contact_ids.mapped(
                    "subscription_list_ids"
                ).mapped("list_id")
                membership.on_mailing_list = (
                    membership.group_id.mailing_list_id in related_lists
                )

    def _inverse_on_mailing_list(self):
        mailing_contact_obj = self.env["mailing.contact"]
        for membership in self:
            related_contacts = mailing_contact_obj.search(
                [("partner_id", "=", membership.partner_id.id)]
            )
            if membership.on_mailing_list:
                if not related_contacts:
                    related_contacts = mailing_contact_obj.create(
                        {"email": membership.partner_id.email}
                    )
                membership.group_id.mailing_list_id.write(
                    {"contact_ids": [(4, related_contacts[0].id)]}
                )
            elif related_contacts:
                membership.group_id.mailing_list_id.write(
                    {"contact_ids": [(3, c.id) for c in related_contacts]}
                )
