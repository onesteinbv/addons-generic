from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def name_get(self):
        res = []
        for user in self:
            if (
                user.partner_id
                and user.partner_id.nickname
                and not user.partner_id.website_published
            ):
                res.append((user.id, user.partner_id.nickname))
            else:
                res.append(super(ResUsers, user).name_get()[0])
        return res
