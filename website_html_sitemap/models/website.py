from odoo import models


class Website(models.Model):
    _inherit = "website"

    def get_website_page_from_url(self, url):
        self.ensure_one()

        WebsitePage = self.env["website.page"]
        domain = [
            ("website_id", "in", (False, self.id)),
            ("url", "=", url),
            ("website_indexed", "=", True),
        ]

        # We must use filtered here, because website_published may be a
        # computed field.
        found_res = WebsitePage.search(domain).filtered(lambda r: r.website_published)
        if not found_res:
            return WebsitePage

        if len(found_res) == 1:
            return found_res

        website_specific = found_res.filtered(lambda r: r.website_id)
        if len(website_specific) == 1:
            return website_specific

        not_website_specific = found_res.filtered(lambda r: not r.website_id)
        if len(not_website_specific) == 1:
            return not_website_specific

        return WebsitePage
