import urllib

from odoo.addons.website_two_steps_share_technical.controllers.main import (
    ShareController,
)


class MainController(ShareController):
    def compute_default_values(self, platform):
        if platform == "diaspora":
            return {
                "service_name": "Diaspora",
                "service_icon_url": "/website_share_diaspora/static/img/icons/diaspora.svg",
                "default_domain": "",
            }
        return super().compute_default_values(platform)

    def compose_final_url(self, kwargs):
        if kwargs["platform"] == "diaspora":
            base_url = kwargs["domain"]
            args_dict = {"url": kwargs["url"], "title": kwargs["title"]}
            url_parts = list(urllib.parse.urlparse(base_url))
            url_parts[2] = "/bookmarklet"
            url_parts[4] = urllib.parse.urlencode(args_dict)
            final_url = urllib.parse.urlunparse(url_parts)
            return final_url
        return super().compose_final_url(kwargs)
