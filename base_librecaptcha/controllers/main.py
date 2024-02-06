from io import BytesIO

from odoo.http import Controller, request, route

try:
    from werkzeug.utils import send_file as _send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file as _send_file


class MainController(Controller):
    @route("/captcha/media", type="http", auth="public", methods=["GET"])
    def media(self, **kw):
        """Obscure that we're using librecaptcha and what server 🤫
        This we also can keep the lc server unexposed 🤩
        """
        mimetype = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("base_librecaptcha.media", "image/gif")
        )
        media = request.env["librecaptcha"].media(kw.get("id"))
        if not media:
            return request.not_found()
        return _send_file(
            BytesIO(media), mimetype=mimetype, environ=request.httprequest.environ
        )

    @route("/captcha", type="json", auth="public", methods=["POST"])
    def captcha(self):
        """Obscure that we're using librecaptcha and what server 🤫"""
        return request.env["librecaptcha"].captcha()
