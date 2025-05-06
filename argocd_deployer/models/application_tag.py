from odoo import fields, models


class ApplicationTag(models.Model):
    _name = "argocd.application.tag"
    _description = "Application Tag"

    name = fields.Char(required=True)
    key = fields.Char(required=True, copy=False)
    is_odoo_module = fields.Boolean(string="Is additional Odoo Module")

    _sql_constraints = [("application_tag_key_unique", "unique(key)", "Already exists")]
