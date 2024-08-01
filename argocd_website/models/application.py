import logging

import requests
import yaml
from yaml import Loader

from odoo import _, fields, models
from odoo.exceptions import MissingError, ValidationError

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
            config = yaml.load(self.config, Loader=Loader)
            helm = yaml.load(config["helm"], Loader=Loader)
            res = requests.get("https://%s" % self._get_domain(helm))
        except Exception:
            return False
        return res.ok

    def dns_cname_check(self, domain, tag_id=None):
        """
        Check if the CNAME record is configured correctly.

        @param domain: Domain name to check
        @param tag_id: argocd.application.tag must be in tag_ids
        @raise: ValidationError: CNAME record configured incorrectly
        @raise: MissingError: Tag is not linked to app
        @return: True
        """
        self.ensure_one()
        expected_subdomain = None
        if tag_id:
            tag = self.tag_ids.filtered(lambda t: t.id == tag_id)
            if not tag:
                raise MissingError(_("Tag is not linked to app"))
            expected_subdomain = tag.key
        default_domain = self.format_domain(subdomain=expected_subdomain)
        expected_content = name.from_text(default_domain)
        res = resolver.resolve(domain, "CNAME")
        record = res[0]
        if expected_content != record.target:
            raise ValidationError(
                _(
                    "CNAME record incorrectly configured expected %(expected_domain)s got %(result)s",
                    expected_domain=default_domain,
                    result=record.target.to_text(),
                )
            )
        return True
