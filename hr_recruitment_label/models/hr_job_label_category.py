from odoo import fields, models


class HrJobCategory(models.Model):
    _name = "hr.job.label.category"
    _rec_name = "name"
    _order = "sequence"

    sequence = fields.Integer()
    name = fields.Char(translate=True, required=1)
    color = fields.Integer()
    label_ids = fields.One2many(comodel_name="hr.job.label", inverse_name="category_id")
