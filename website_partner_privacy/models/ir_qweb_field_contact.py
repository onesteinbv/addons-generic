from odoo import api, models


class Contact(models.AbstractModel):
    _inherit = "ir.qweb.field.contact"

    @api.model
    def value_to_html(self, value, options):
        if not value:
            return ""
        if self._context.get("website_id"):
            if not options.get("fields"):
                options.update(
                    {"fields": ["name", "address", "phone", "mobile", "email"]}
                )
            if hasattr(value, "show_email") and not value.show_email:
                "email" in options["fields"] and options["fields"].remove("email")
            if hasattr(value, "show_address") and not value.show_address:
                "address" in options["fields"] and options["fields"].remove("address")
            if hasattr(value, "show_phone") and not value.show_phone:
                "phone" in options["fields"] and options["fields"].remove("phone")
                "mobile" in options["fields"] and options["fields"].remove("mobile")
            if hasattr(value, "show_website") and not value.show_website:
                "website" in options["fields"] and options["fields"].remove("website")
            if not options.get("fields"):
                options.update(
                    {"fields": [""]}
                )  # hack to make sure fields are not updated to all from base function
        return super().value_to_html(value, options)
