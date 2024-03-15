from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.auth_signup.models.res_partner import random_token


class SaleSubscription(models.Model):
    _name = "sale.subscription"
    _inherit = [
        "sale.subscription",
        "portal.mixin",
    ]

    deletion_token = fields.Char()
    deletion_token_expiration = fields.Datetime()

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/subscriptions/{}".format(record.id)

    def start_cancellation(self):
        self.ensure_one()
        self.deletion_token = random_token()
        self.deletion_token_expiration = fields.Datetime.now() + timedelta(days=1)

        template = self.env.ref("argocd_website.delete_request_mail_template")
        template.send_mail(self.id)

    def confirm_cancellation(self, token, close_reason_id=False):
        self.ensure_one()
        if self.deletion_token != token:
            raise ValidationError(_("Invalid token"))
        if fields.Datetime.now() > self.deletion_token_expiration:
            raise ValidationError(_("Token expired"))

        self.deletion_token = False
        self.deletion_token_expiration = False

        self.close_subscription(close_reason_id)
