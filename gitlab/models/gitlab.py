from odoo import _, fields, models

import gitlab


class Gitlab(models.Model):
    _name = "gitlab"
    _description = "Gitlab Connection"

    url = fields.Char(string="URL", default="https://gitlab.com")
    private_token = fields.Char(string="Private / Personal Token", required=True)
    debug = fields.Boolean(string="Enable Debug Mode")
    per_page = fields.Integer(string="Pagination", default=100)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.url))
        return res

    def get_server_connection(self):
        self.ensure_one()
        gl = gitlab.Gitlab(url=self.url, private_token=self.private_token)
        if self.debug:
            gl.enable_debug()
        return gl

    def validate(self):
        gl = self.get_server_connection()
        gl.auth()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": _("Connection Test Successful"), "type": "success"},
        }
