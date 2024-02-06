import urllib

from odoo.addons.website_two_steps_share_technical.controllers.main import (
    ShareController,
)


class MainController(ShareController):
    def compute_default_values(self, platform):
        if platform == "pleroma":
            return {
                "service_name": "Pleroma",
                "service_icon_url": "/website_share_pleroma/static/img/icons/pleroma.svg",
                "default_domain": "",
            }
        return super().compute_default_values(platform)

    def compose_final_url(self, kwargs):
        if kwargs["platform"] == "pleroma":
            base_url = kwargs["domain"]
            args_dict = {
                "status_textarea": "{} {}".format(kwargs["title"], kwargs["url"])
            }
            url_parts = list(urllib.parse.urlparse(base_url))
            url_parts[2] = "/notice/new"
            url_parts[4] = urllib.parse.urlencode(args_dict)
            final_url = urllib.parse.urlunparse(url_parts)
            return final_url
        return super().compose_final_url(kwargs)
