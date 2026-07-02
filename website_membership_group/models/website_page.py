from odoo import models


class WebsitePage(models.Model):
    _inherit = "website.page"

    def write(self, vals):
        res = super().write(vals)
        if "is_published" in vals:
            for page in self:
                linked_groups = (
                    self.env["membership.group"]
                    .sudo()
                    .search(
                        [
                            ("page_id", "=", page.id),
                            ("is_published", "!=", page.is_published),
                        ]
                    )
                )
                if linked_groups:
                    linked_groups.write({"is_published": page.is_published})
        return res
