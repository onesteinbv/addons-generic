from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    github_login = fields.Char(string="Github Username")

    @api.model
    def get_id_by_github_login(self, github_login):
        return self.search([("github_login", "=ilike", github_login)], limit=1).id
