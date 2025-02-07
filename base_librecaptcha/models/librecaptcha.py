import json
import logging

import requests

from odoo import _, http, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LibreCaptcha(models.AbstractModel):
    _name = "librecaptcha"
    _description = "LibreCaptcha"

    def captcha(self):
        if not self.is_enabled():
            return http.request.make_response(
                data=json.dumps({"error": "Captcha is not enabled"}),
                status=400,
            )

        url, level, media, input_type = self._get_config().values()

        resp = requests.post(
            f"{url}/v2/captcha",
            json={
                "level": level,
                "media": media,
                "input_type": input_type,
                "size": "350x100",
            },
        )

        if resp.ok:
            return resp.json()["id"]

        error = "captcha failed with code %s: %s" % (resp.status_code, resp.text)
        _logger.error(error)
        raise Exception(error)

    def media(self, captcha_id):
        url = self._get_config().get("url")

        resp = requests.get(
            f"{url}/v2/media",
            params={
                "id": captcha_id,
            },
        )

        if resp.ok:
            return resp.content

    def answer(self, captcha_id, answer, raise_exception=False):
        url = self._get_config().get("url")
        resp = requests.post(
            f"{url}/v2/answer",
            json={
                "id": captcha_id,
                "answer": answer,
            },
        )

        if resp.ok:
            result = resp.json()["result"]
            if raise_exception:
                if result == "False":
                    raise UserError(_("Captcha incorrect."))
                if result == "Expired":
                    raise UserError(_("Captcha Expired."))
            return result

        error = "librecaptcha failed with code %s: %s" % (resp.status_code, resp.text)
        _logger.error(error)
        raise Exception(error)

    def is_enabled(self):
        return self._get_config_record().librecaptcha_enabled

    def _get_config_record(self):
        """method to be inherit to change the config record"""
        return self.env.company

    def _get_config(self):
        if not self.is_enabled():
            return {}

        record = self._get_config_record()

        return {
            "url": record.librecaptcha_url,
            "level": record.librecaptcha_level,
            "media": f"image/{record.librecaptcha_media}",
            "input_type": record.librecaptcha_type,
        }
