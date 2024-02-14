from odoo import fields, models


class HrJobLabelCategory(models.Model):
    _inherit = "hr.job.label.category"

    allow_filtering = fields.Boolean(
        default=True,
        help="Disable showing this category on the filter options on the website",
    )
