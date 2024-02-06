from odoo.tests import TransactionCase


class TestWebsite(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website1 = cls.env["website"].create({"name": "Foo"})
        cls.website2 = cls.env["website"].create({"name": "Bar"})

    def test_get_website_page_from_url(self):
        """Get website page from URL returns the correct website page."""
        WebsitePage = self.env["website.page"]
        website_page_1 = WebsitePage.create(
            {
                "url": "/ultimate_test_page",
                "is_published": False,
                "website_indexed": False,
                "website_id": False,
                "name": "The Ultimate Test Page",
                "view_id": self.env.ref("base.res_partner_kanban_view").id,
            }
        )
        with self.subTest(msg="Not published"):
            lookup = self.website1.get_website_page_from_url("/ultimate_test_page")
            self.assertFalse(lookup)

        website_page_1.is_published = True
        with self.subTest(msg="Published, not indexed"):
            lookup = self.website1.get_website_page_from_url("/ultimate_test_page")
            self.assertFalse(lookup)
            lookup = self.website2.get_website_page_from_url("/ultimate_test_page")
            self.assertFalse(lookup)

        website_page_1.website_indexed = True
        with self.subTest(msg="Published and indexed"):
            lookup = self.website1.get_website_page_from_url("/ultimate_test_page")
            self.assertEqual(website_page_1, lookup)
            lookup = self.website2.get_website_page_from_url("/ultimate_test_page")
            self.assertEqual(website_page_1, lookup)

        website_page_1.website_id = self.website1
        with self.subTest(msg="Published and indexed on specific website"):
            lookup = self.website1.get_website_page_from_url("/ultimate_test_page")
            self.assertEqual(website_page_1, lookup)
            lookup = self.website2.get_website_page_from_url("/ultimate_test_page")
            self.assertFalse(lookup)

        website_page_2 = WebsitePage.create(
            {
                "url": "/ultimate_test_page",
                "is_published": True,
                "website_indexed": True,
                "website_id": False,
                "view_id": self.env.ref("base.view_ir_config_form").id,
            }
        )
        with self.subTest(msg="Same url, published and indexed on different website"):
            lookup = self.website1.get_website_page_from_url("/ultimate_test_page")
            self.assertEqual(website_page_1, lookup)
            lookup = self.website2.get_website_page_from_url("/ultimate_test_page")
            self.assertEqual(website_page_2, lookup)
