from odoo import api, fields, models


class MembershipSectionMembership(models.Model):
    _inherit = "membership.section.membership"

    on_mailing_list = fields.Boolean(
        compute="_compute_on_mailing_list",
        inverse="_inverse_on_mailing_list",
        store=True,
        readonly=False,
    )

    @api.depends(
        "section_id",
        "section_id.mailing_list_id",
        "partner_id",
        "partner_id.mass_mailing_contact_ids",
    )
    def _compute_on_mailing_list(self):
        for membership in self:
            if (
                not membership.section_id
                or not membership.section_id.mailing_list_id
                or not membership.partner_id
            ):
                membership.on_mailing_list = False
            else:
                related_contacts = membership.partner_id.mass_mailing_contact_ids
                related_lists = related_contacts.mapped("subscription_list_ids").mapped(
                    "list_id"
                )
                if membership.section_id.mailing_list_id in related_lists:
                    membership.on_mailing_list = True
                else:
                    membership.on_mailing_list = False

    def _inverse_on_mailing_list(self):
        for membership in self:
            related_contacts = self.env["mailing.contact"].search(
                [("partner_id", "=", membership.partner_id.id)]
            )
            if membership.on_mailing_list:
                if not related_contacts:
                    related_contact = self.env["mailing.contact"].create(
                        {"email": membership.partner_id.email}
                    )
                else:
                    related_contact = related_contacts[0]
                membership.section_id.mailing_list_id.write(
                    {"contact_ids": [(4, related_contact.id)]}
                )
            else:
                if related_contacts:
                    membership.section_id.mailing_list_id.write(
                        {"contact_ids": [(3, c.id) for c in related_contacts]}
                    )
