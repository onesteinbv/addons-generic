from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.auth_signup.models.res_partner import random_token


class SaleSubscription(models.Model):
    _name = "sale.subscription"
    _inherit = [
        "sale.subscription",
        "portal.mixin",
    ]

    date_stop = fields.Date(
        help="The last date we need to provide the service",
        string="Last date of service",
        readonly=True,
    )
    cancellation_token = fields.Char()
    cancellation_token_expiration = fields.Datetime()

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/subscriptions/{}".format(record.id)

    def action_start_subscription(self):
        self.date_stop = False
        return super().action_start_subscription()

    def start_cancellation(self):
        self.ensure_one()
        self.cancellation_token = random_token()
        self.cancellation_token_expiration = fields.Datetime.now() + timedelta(days=1)
        if not self.in_progress:
            raise UserError(_("Subscription is not in progress."))

        template = self.env.ref("subscription_portal.cancel_subscription_mail_template")
        template.send_mail(self.id, email_values={"is_internal": True})

    def confirm_cancellation(self, token, close_reason_id=False):
        self.ensure_one()
        if self.cancellation_token != token:
            raise ValidationError(_("Invalid token"))
        if fields.Datetime.now() > self.cancellation_token_expiration:
            raise ValidationError(_("Token expired"))

        self.cancellation_token = False
        self.cancellation_token_expiration = False

        self.close_subscription(close_reason_id)
