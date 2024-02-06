from odoo import models
from odoo.http import request


def _monkey_patch_set_cookie(response):
    set_cookie = response.set_cookie

    def _set_cookie(
        key,
        value="",
        max_age=None,
        expires=None,
        path="/",
        domain=None,
        secure=False,
        httponly=False,
        samesite=None,
    ):
        if key != "session_id":
            return set_cookie(
                key, value, max_age, expires, path, domain, secure, httponly, samesite
            )

    return _set_cookie


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        response = super()._dispatch(endpoint)
        if (
            hasattr(response, "mimetype")
            and response.mimetype in ("text/html", "image/jpeg", "image/png")
            and request.httprequest.method == "GET"
        ):
            is_public_user = (
                hasattr(request, "website") and request.env["website"].is_public_user()
            )
            if not is_public_user or request.httprequest.path.startswith("/web"):
                response.headers["Cache-Control"] = "No-Cache"
                response.set_cookie("odoo_backend", request.httprequest.session.sid)
            else:
                response.headers.pop("Set-Cookie", None)
                response.set_cookie = _monkey_patch_set_cookie(response)
        return response
