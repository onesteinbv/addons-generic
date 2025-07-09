from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    website_privacy = fields.Selection(
        selection="website_privacy_selection",
        default="name",
        required=True,
        string="Website Privacy Level",
        help="Select which option to use to display partners on Website",
    )
    show_email = fields.Boolean(default=False, help="Show/Hide Email On Website")
    show_address = fields.Boolean(default=False, help="Show/Hide Address On Website")
    show_phone = fields.Boolean(default=False, help="Show/Hide Phone On Website")
    show_website = fields.Boolean(default=False, help="Show/Hide Website On Website")

    def website_privacy_selection(self):
        return [("anonymous", "Stay Anonymous"), ("name", "Use Name")]

    @api.model_create_multi
    def create(self, values_list):
        for vals in values_list:
            if "website_privacy" in vals and vals["website_privacy"] == "anonymous":
                vals.update({"seo_name": "Anonymous", "is_published": False})
        return super().create(values_list)

    def write(self, vals):
        if "website_privacy" in vals:
            if vals["website_privacy"] == "anonymous":
                vals.update({"seo_name": "Anonymous", "is_published": False})
            elif vals["website_privacy"] == "name":
                vals.update({"seo_name": False})
        return super().write(vals)

    @api.onchange("website_privacy")
    def onchange_website_privacy(self):
        if self.website_privacy == "anonymous":
            self.is_published = False

    def _get_name(self):
        name = super(ResPartner, self)._get_name()
        if self._context.get("website_id"):
            if self.website_privacy and self.website_privacy == "anonymous":
                name = "Anonymous"
        return name
