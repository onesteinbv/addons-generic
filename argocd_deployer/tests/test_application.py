from odoo import Command
from odoo.tests.common import TransactionCase


class TestApplication(TransactionCase):
    def test_get_urls(self):
        app = self.env["argocd.application"].create(
            {
                "name": "myapp",
                "template_id": self.ref(
                    "argocd_deployer.demo_curq_basis_application_template"
                ),
                "tag_ids": [
                    self.ref("argocd_deployer.demo_matomo_server_application_tag")
                ],
            }
        )
        app.render_config()
        urls = app.get_urls()
        expected_urls = [
            ("https://myapp.curq.k8s.onestein.eu", "Odoo"),
            ("https://matomo.myapp.curq.k8s.onestein.eu", "Matomo Server"),
        ]
        self.assertEqual(urls, expected_urls)

        app.tag_ids = [Command.clear()]
        app.render_config()
        urls = app.get_urls()
        expected_urls = [("https://myapp.curq.k8s.onestein.eu", "Odoo")]
        self.assertEqual(urls, expected_urls)
