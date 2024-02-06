from datetime import timedelta

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.auth_signup.models.res_partner import random_token


class Application(models.Model):
    _name = "argocd.application"
    _inherit = ["argocd.application", "portal.mixin"]

    deletion_token = fields.Char()
    deletion_token_expiration = fields.Datetime()

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/applications/{}".format(record.id)

    def check_health(self):
        self.ensure_one()
        try:
            res = requests.get("https://" + self.domain)
        except Exception:
            return False
        return res.ok

    def request_destroy(self):
        # We don't want user to easily delete their applications
        self.ensure_one()
        self.deletion_token = random_token()
        self.deletion_token_expiration = fields.Datetime.now() + timedelta(days=1)

        template = self.env.ref("argocd_website.delete_request_mail_template")
        template.send_mail(self.id)

    def confirm_destroy(self, token):
        self.ensure_one()
        if self.deletion_token != token:
            raise ValidationError(_("Invalid token"))
        if fields.Datetime.now() > self.deletion_token_expiration:
            raise ValidationError(_("Token expired"))

        self.deletion_token = False
        self.deletion_token_expiration = False

        # Destroy and delete app record
        self.destroy()
