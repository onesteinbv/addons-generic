from unittest.mock import patch

from odoo.http import Response, route
from odoo.tests import TransactionCase, tagged

from ._simple_mock_request import SimpleMockRequest


@tagged("post_install", "-at_install")
class TestIrHttp(TransactionCase):
    def setUp(self):
        super().setUp()
        self.test_endpoint_call_count = 0

    @route(["/test"], type="http", auth="public", website=True, sitemap=True)
    def _test_endpoint(self):
        """This endpoint simulates a controller that can be used in the dispatch
        method."""
        self.test_endpoint_call_count += 1
        return Response(
            "",
            status=200,
            mimetype="text/html",
            content_type="text/html;charset=utf-8",
            headers={"Set-Cookie": "true"},
        )

    def test_dispatch_is_called(self):
        """The overridden dispatch method is called when calling ir.http._dispatch()"""
        website = self.env.ref("website.default_website").with_user(
            self.env.ref("base.public_user")
        )
        with SimpleMockRequest(
            website.env, website=website, method="GET", path="/hello"
        ):
            response = self.env["ir.http"]._dispatch(self._test_endpoint)
            self.assertEqual(1, self.test_endpoint_call_count)
            expected = {
                "Content-Type": "text/html;charset=utf-8",
                "Content-Length": "0",
                "Set-Cookie": True,
            }
            for key, value in response.headers.items():
                self.assertEqual(expected[key], value)

    def test_cache_ignore(self):
        """If the response is not a PNG, JPEG, or html, or the request is not a GET
        request then nothing should happen."""
        website = self.env.ref("website.default_website").with_user(
            self.env.ref("base.public_user")
        )
        with SimpleMockRequest(
            website.env, website=website, method="PUT", path="/hello"
        ):
            response = self.env["ir.http"]._dispatch(self._test_endpoint)
            self.assertEqual(1, self.test_endpoint_call_count)
            # This was set in the endpoint, so should still be there.
            self.assertEqual("true", response.headers.get("Set-Cookie"))

    @patch("odoo.http.Response.set_cookie")
    def test_cache_disable(self, set_cookie_method):
        """If the response is a PNG, JPEG, or html as a result for a GET request
        by an authenticated user, then caching should be disabled."""
        website = self.env.ref("website.default_website")
        with SimpleMockRequest(self.env, website=website, method="GET"):
            response = self.env["ir.http"]._dispatch(self._test_endpoint)
            self.assertEqual(1, self.test_endpoint_call_count)
            self.assertEqual("No-Cache", response.headers["Cache-Control"])
            set_cookie_method.assert_called_once()

    @patch("odoo.http.Response.set_cookie")
    def test_cache_enable(self, set_cookie_method):
        """If the response is a PNG, JPEG, or html as a result for a GET request
        by a public user, then the Set-Cookie header should be removed, and the
        set_cookie method should be monkey-patched."""
        website = self.env.ref("website.default_website").with_user(
            self.env.ref("base.public_user")
        )
        with SimpleMockRequest(
            website.env, website=website, method="GET", path="/hello"
        ):
            response = self.env["ir.http"]._dispatch(self._test_endpoint)
            self.assertEqual(1, self.test_endpoint_call_count)
            self.assertEqual(None, response.headers.get("Set-Cookie"))

            # The set_cookie method on the response should have been monkey patched.
            # So we're going to test if it's functioning. The monkey patch prevents
            # the regular set_cookie method from being called when the key is
            # "session_id"
            response.set_cookie(
                key="session_id", value=7, max_age=60, httponly=True, samesite="Lax"
            )
            set_cookie_method.assert_not_called()
            response.set_cookie(
                key="hello", value=7, max_age=60, httponly=True, samesite="Lax"
            )
            set_cookie_method.assert_called_once()
