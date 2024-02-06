import logging

import requests

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LibreCaptcha(models.AbstractModel):
    _name = "librecaptcha"
    _description = "LibreCaptcha"

    def captcha(self):
        url = self.env["ir.config_parameter"].sudo().get_param("base_librecaptcha.url")
        level = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_librecaptcha.level", "hard")
        )
        media = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_librecaptcha.media", "image/gif")
        )

        resp = requests.post(
            "%s/v2/captcha" % url,
            json={
                "level": level,
                "media": media,
                "input_type": "text",
                "size": "350x100",
            },
        )

        if resp.ok:
            return resp.json()["id"]

        error = "librecaptcha failed with code %s: %s" % (resp.status_code, resp.text)
        _logger.error(error)

        raise Exception(error)

    def media(self, captcha_id):
        url = self.env["ir.config_parameter"].sudo().get_param("base_librecaptcha.url")

        resp = requests.get(
            "%s/v2/media" % url,
            params={
                "id": captcha_id,
            },
        )

        if resp.ok:
            return resp.content

    def answer(self, captcha_id, answer, raise_exception=False):
        url = self.env["ir.config_parameter"].sudo().get_param("base_librecaptcha.url")
        resp = requests.post(
            "%s/v2/answer" % url, json={"id": captcha_id, "answer": answer}
        )

        if resp.ok:
            result = resp.json()["result"]
            if raise_exception:
                if result == "False":
                    raise ValidationError(_("Captcha incorrect."))
                if result == "Expired":
                    raise ValidationError(_("Captcha Expired."))
            return result

        error = "librecaptcha failed with code %s: %s" % (resp.status_code, resp.text)
        _logger.error(error)
        raise Exception(error)

    def is_enabled(self):
        return bool(
            self.env["ir.config_parameter"].sudo().get_param("base_librecaptcha.url")
        )
