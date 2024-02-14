# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrJobLabel(models.Model):
    _name = "hr.job.label"
    _order = "sequence,category_id"
    _rec_name = "rec_name"

    rec_name = fields.Char(compute="_compute_rec_name", store=True)

    sequence = fields.Integer()
    category_id = fields.Many2one(comodel_name="hr.job.label.category", required=1)
    name = fields.Char(translate=True, required=1)
    color = fields.Integer(related="category_id.color")

    @api.depends("category_id", "category_id.name", "name")
    def _compute_rec_name(self):
        for label in self:
            label.rec_name = "%(categ_name)s: %(label_name)s" % {
                "categ_name": label.category_id.name,
                "label_name": label.name,
            }

    _sql_constraints = [
        (
            "name_uniq",
            "unique (name,categ_id)",
            "Label name already exists within " "this category!",
        ),
    ]


class HrJobCategory(models.Model):
    _name = "hr.job.label.category"
    _rec_name = "name"

    name = fields.Char(translate=True, required=1)
    color = fields.Integer()
    label_ids = fields.One2many(comodel_name="hr.job.label", inverse_name="category_id")
