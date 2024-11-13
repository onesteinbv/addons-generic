from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    github_login = fields.Char(string="Github Username")
    gitlab_email = fields.Char(help="Can be used to reconcile commits")
    gitlab_username = fields.Char(
        help="Can be used to reconcile merge requests, issues, comment, and reviews",
    )
