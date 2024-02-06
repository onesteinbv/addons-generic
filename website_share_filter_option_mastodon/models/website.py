from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    share_mastodon = fields.Boolean(default=True)

    def get_exclude_share_links(self, default=None):
        self.ensure_one()
        res = super(Website, self).get_exclude_share_links(default=default or [])
        if not self.share_mastodon:
            res.append("mastodon")
        return res
