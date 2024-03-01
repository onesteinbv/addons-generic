import logging
from datetime import timedelta

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.auth_signup.models.res_partner import random_token

_logger = logging.getLogger(__name__)

try:
    from dns import name, resolver
except ImportError as err:
    _logger.debug(err)


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

    def dns_cname_check(self, domain, expected_subdomain=None):
        """
        Check if the CNAME record is configured correctly.

        @param domain: Domain name to check
        @param expected_subdomain: Subdomain to expect when resolving CNAME for domain
        @raise: ValidationError: CNAME record configured incorrectly
        @return: True
        """
        self.ensure_one()
        expected_domain = self.format_domain(subdomain=expected_subdomain)
        expected_content = name.from_text(expected_domain)
        res = resolver.resolve(domain, "CNAME")

        record = res[0]
        if expected_content != record.target:
            raise ValidationError(
                _(
                    "CNAME record incorrectly configured expected %(expected_domain)s got %(result)s",
                    expected_domain=expected_domain,
                    result=record.target.to_text(),
                )
            )
        return True
