from odoo import api, fields, models


class MembershipActivity(models.Model):
    _inherit = "membership.activity"

    github_login = fields.Char()

    @api.depends("github_login")
    def _compute_partner_id(self):
        result = super()._compute_partner_id()

        login_map = {}
        for activity in self.filtered(lambda a: a.github_login):
            if activity.github_login not in login_map:
                login_map[activity.github_login] = self.env[
                    "res.partner"
                ].get_id_by_github_login(activity.github_login)
            activity.partner_id = login_map[activity.github_login]

        return result
