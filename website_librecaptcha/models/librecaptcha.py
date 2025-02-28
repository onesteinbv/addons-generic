from odoo import http, models


class LibreCaptcha(models.AbstractModel):
    _inherit = "librecaptcha"

    def _get_config_record(self):
        ret = super()._get_config_record()

        # at early level the website is not loaded in the request
        if hasattr(http.request, "website"):
            return ret and http.request.website

        return ret
