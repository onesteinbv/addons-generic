from odoo import fields, models


class HrJobLabelCategory(models.Model):
    _inherit = "hr.job.label.category"

    allow_filtering = fields.Boolean(
        default=True,
        help="Disable showing this category on the filter options on the website",
    )
    show_on_website = fields.Boolean(
        default=True,
        help="Decides if these tags get shown on the job cards",
    )
