import re

from odoo import http
from odoo.http import request


class ShareController(http.Controller):
    def compute_default_values(self, platform):
        return {
            "service_name": "",
            "service_icon_url": "",
            "default_domain": "",
        }

    def compose_final_url(self, kwargs):
        return ""

    @http.route(
        ["/share/getDomain"],
        type="http",
        website=True,
        auth="public",
        methods=["GET"],
        sitemap=False,
    )
    def share_ask_domain(self, **kwargs):
        render_vals = {
            "url": kwargs["url"].strip(),
            "platform": kwargs["platform"],
            "title": kwargs["title"].strip(),
            "media": kwargs["media"],
        }
        render_vals.update(self.compute_default_values(kwargs["platform"]))
        return request.render(
            "website_two_steps_share_technical.custom_share_form", render_vals
        )

    @http.route(
        ["/share/confirm"],
        type="http",
        website=True,
        auth="public",
        methods=["GET"],
        sitemap=False,
    )
    def share_redirect(self, **kwargs):
        def formaturl(url):
            if not re.match("(?:http|ftp|https)://", url):
                return "https://{}".format(url)
            return url

        kwargs["domain"] = formaturl(kwargs["domain"])
        url = self.compose_final_url(kwargs)
        return request.redirect(url, local=False)
