from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    nickname = fields.Char()

    @api.model
    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = list(args or [])
        if name:
            args += ["|", ("name", operator, name), ("nickname", operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
