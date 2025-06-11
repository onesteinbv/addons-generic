from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    gitlab_email = fields.Char(help="Used to reconcile commits")
    gitlab_username = fields.Char(
        help="Used to reconcile merge requests, issues, comment, and reviews",
    )

    @api.model
    def get_id_by_gitlab_email(self, gitlab_email):
        return self.search(
            [
                "|",
                ("gitlab_email", "=ilike", gitlab_email),
                ("email", "=ilike", gitlab_email),
            ],
            limit=1,
        ).id

    @api.model
    def get_id_by_gitlab_username(self, gitlab_username):
        return self.search([("gitlab_username", "=ilike", gitlab_username)], limit=1).id
