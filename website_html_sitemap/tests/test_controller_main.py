import logging

from odoo.tests import tagged
from odoo.tests.common import HttpCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestControllerMain(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = "/sitemap"
        cls.website1 = cls.env["website"].create({"name": "Foo"})
        cls.website2 = cls.env["website"].create({"name": "Bar"})

    def test_base_sitemap(self):
        """HTML sitemap works."""
        response = self.url_open(
            self.url,
        )
        response.raise_for_status()

    def test_sitemap_home(self):
        """HTML sitemap works."""
        response = self.url_open(
            self.url,
        )
        response.raise_for_status()
        self.assertIn(b"Home", response.content)

        WebsitePage = self.env["website.page"]
        WebsitePage.create(
            {
                "url": "/ultimate_test_page",
                "is_published": True,
                "website_indexed": True,
                "website_id": False,
                "name": "The Ultimate Test Page",
                "view_id": self.env.ref("base.res_partner_kanban_view").id,
            }
        )
        response = self.url_open(
            self.url,
        )
        response.raise_for_status()
        self.assertIn(b"The Ultimate Test Page", response.content)

        WebsitePage.create(
            {
                "url": "/ultimate_test_page2",
                "is_published": True,
                "website_indexed": True,
                "website_id": False,
                "view_id": self.env.ref("base.view_partner_address_form").id,
            }
        )
        response = self.url_open(
            self.url,
        )
        response.raise_for_status()
        self.assertIn(b"The Ultimate Test Page", response.content)
        self.assertIn(b"ultimate_test_page2", response.content)
