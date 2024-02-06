from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self.filtered(
            lambda x: x.line_ids.filtered(
                lambda y: y.product_id
                and y.product_id.membership
                and y.product_id.type == "service"
            )
        ):
            partner = move.partner_id
            if partner.membership_email_verification_status == "unverified":
                partner.verify_email(partner.email, partner.email_verification_token)
            if not partner.user_ids or (
                not any(user.has_group("base.group_user") for user in partner.user_ids)
                and not any(
                    user.has_group("base.group_portal") for user in partner.user_ids
                )
            ):
                wizard = (
                    self.env["portal.wizard"]
                    .with_user(self.env.ref("base.user_admin").id)
                    .create(
                        {
                            "partner_ids": [(6, 0, partner.ids)],
                        }
                    )
                )
                wizard.user_ids.action_grant_access()
                partner.create_member_applicant()
        return res
