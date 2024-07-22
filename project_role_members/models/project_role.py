from odoo import fields, models


class ProjectRole(models.Model):
    _inherit = "project.role"

    is_manager = fields.Boolean()
