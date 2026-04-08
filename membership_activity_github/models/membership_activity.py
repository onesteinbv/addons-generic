from odoo import api, fields, models


class MembershipActivity(models.Model):
    _inherit = "membership.activity"

    github_login = fields.Char()

    def init(self):
        super().init()
        # Create an index to speed up searching for duplicate activities
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS membership_activity_github_url_project_type_index
            ON membership_activity (url, project_id, type_id)
            """
        )

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
