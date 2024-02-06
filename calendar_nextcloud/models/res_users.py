from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    caldav_nextcloud = fields.Boolean()
