from itertools import islice

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import LOC_PER_SITEMAP


class MainController(http.Controller):
    @http.route(
        ["/sitemap"],
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
        sitemap=True,
    )
    def sitemap(self):
        locs = (
            request.website.with_context(_filter_duplicate_pages=True)
            .with_user(request.website.user_id)
            ._enumerate_pages()
        )
        locs_list = [loc for loc in locs]
        website_sudo = request.website.sudo()
        for loc in locs_list:
            res = website_sudo.get_website_page_from_url(loc["loc"])
            if res:
                loc["res"] = res
                loc["display"] = res.display_name
            else:
                loc["display"] = loc["loc"]
        sorted_locs = sorted(locs_list, key=lambda l: l["display"])
        sorted_locs = sorted(sorted_locs, key=lambda l: "res" not in l)

        values = {
            "locs": islice(sorted_locs, 0, LOC_PER_SITEMAP),
            "url_root": request.httprequest.url_root[:-1],
        }

        return request.render("website_html_sitemap.sitemap", values)
