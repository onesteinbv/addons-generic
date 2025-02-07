from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import SIGN_UP_REQUEST_PARAMS
from odoo.addons.web.controllers.utils import ensure_db


class CaptchaAuthSignupHome(AuthSignupHome):
    def get_auth_signup_config(self):
        values = super().get_auth_signup_config()
        values["captcha_enabled"] = request.env["librecaptcha"].is_enabled()
        return values

    def _prepare_signup_values(self, qcontext):
        if not qcontext.get("captcha_enabled"):
            return super()._prepare_signup_values(qcontext)

        request.env["librecaptcha"].answer(
            request.params.get("captcha_id"),
            request.params.get("captcha_answer"),
            raise_exception=True,
        )

        return super()._prepare_signup_values(qcontext)

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if request.env.uid is None:
            if request.session.uid is None:
                # no user -> auth=public with specific website public user
                request.env["ir.http"]._auth_method_public()
            else:
                # auth=user
                request.update_env(user=request.session.uid)

        if not request.env["librecaptcha"].is_enabled():
            return super().web_login(*args, **kw)

        if request.httprequest.method == "POST":
            try:
                request.env["librecaptcha"].answer(
                    request.params.get("captcha_id"),
                    request.params.get("captcha_answer"),
                    raise_exception=True,
                )
            except UserError as e:
                values = {
                    k: v
                    for k, v in request.params.items()
                    if k in SIGN_UP_REQUEST_PARAMS
                }
                values["error"] = str(e)
                values["captcha_enabled"] = True

                response = request.render("web.login", values)
                response.headers["Cache-Control"] = "no-cache"
                response.headers["X-Frame-Options"] = "SAMEORIGIN"
                response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
                return response

        return super().web_login(*args, **kw)
