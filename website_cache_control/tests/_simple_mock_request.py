import contextlib
from unittest.mock import MagicMock, Mock, patch

import werkzeug

import odoo
from odoo.tools.misc import DotDict


@contextlib.contextmanager
def SimpleMockRequest(
    env,
    *,
    website=None,
    method="GET",
    path="/hello",
):
    router = MagicMock()
    match = router.return_value.bind.return_value.match
    match.return_value[0].routing = {"type": "http", "website": True, "multilang": True}

    context = {}
    lang_code = env.context.get("lang", "en_US")
    context.setdefault("lang", lang_code)

    request = Mock(
        context=context,
        db=None,
        endpoint=match.return_value[0],
        env=env,
        httprequest=Mock(
            host="localhost",
            path=path,
            app=odoo.http.root,
            environ={"REMOTE_ADDR": "127.0.0.1"},
            cookies={},
            referrer="",
            method=method,
            user_agent=Mock(string="hello"),
        ),
        lang=env["res.lang"]._lang_get(lang_code),
        redirect=werkzeug.utils.redirect,
        session=DotDict(
            debug=False,
        ),
        website=website,
        render=lambda *a, **kw: "<MockResponse>",
        params={},
    )

    with contextlib.ExitStack() as s:
        odoo.http._request_stack.push(request)
        s.callback(odoo.http._request_stack.pop)
        s.enter_context(patch("odoo.http.root.get_db_router", router))

        yield request
