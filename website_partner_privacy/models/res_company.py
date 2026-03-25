from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    default_website_privacy = fields.Selection(
        selection=lambda r: r.env["res.partner"].website_privacy_selection(),
        default="name",
        required=True,
        string="Default Website Privacy Level",
        help="Select which option to use to display partners on Website",
    )
    default_show_email = fields.Boolean(default=True, help="Show/Hide Email On Website")
    default_show_address = fields.Boolean(
        default=True, help="Show/Hide Address On Website"
    )
    default_show_phone = fields.Boolean(default=True, help="Show/Hide Phone On Website")
    default_show_website = fields.Boolean(
        default=True, help="Show/Hide Website On Website"
    )
