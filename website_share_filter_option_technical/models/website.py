from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    share_facebook = fields.Boolean(default=True)
    share_twitter = fields.Boolean(default=True)
    share_linkedin = fields.Boolean(default=True)
    share_whatsapp = fields.Boolean(default=True)
    share_pinterest = fields.Boolean(default=True)
    share_email = fields.Boolean(default=True)

    def get_exclude_share_links(self, default=None):
        self.ensure_one()
        res = []

        if not self.share_facebook:
            res.append("facebook")
        if not self.share_twitter:
            res.append("twitter")
        if not self.share_linkedin:
            res.append("linkedin")
        if not self.share_whatsapp:
            res.append("whatsapp")
        if not self.share_pinterest:
            res.append("pinterest")
        if not self.share_email:
            res.append("email")

        return list(set(res + (default or [])))
