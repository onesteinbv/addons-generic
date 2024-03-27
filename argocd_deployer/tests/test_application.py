from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


class TestApplication(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = cls.env["argocd.application"].create(
            {
                "name": "myapp",
                "template_id": cls.env.ref(
                    "argocd_deployer.demo_curq_basis_application_template"
                ).id,
                "tag_ids": [
                    cls.env.ref(
                        "argocd_deployer.demo_matomo_server_application_tag"
                    ).id,
                ],
            }
        )

    def test_get_urls(self):
        self.app.render_config()
        urls = {url for url in self.app.get_urls()}
        expected_urls = {
            ("https://myapp.curq.k8s.onestein.eu", "Odoo"),
            ("https://matomo.myapp.curq.k8s.onestein.eu", "Matomo Server"),
        }
        self.assertEqual(expected_urls, urls)

        self.app.tag_ids = [Command.clear()]
        self.app.render_config()
        urls = self.app.get_urls()
        expected_urls = [("https://myapp.curq.k8s.onestein.eu", "Odoo")]
        self.assertEqual(urls, expected_urls)

    def test_immediate_deploy(self):
        mock_repository = MagicMock()
        mock_remote = MagicMock()
        mock_repository.remotes.origin = mock_remote
        mock_repository.working_dir = "/home/test"
        mock_get_repository = MagicMock(return_value=mock_repository)
        mock_deploy_files = MagicMock(
            return_value=({"add": "test.yaml"}, "Added `%s`.)")
        )

        # We're already patching here, so we don't have to simulate.
        simulate_commit = safe_eval(
            self.env["ir.config_parameter"].get_param("argocd.simulate_commit", False)
        )
        if simulate_commit:
            self.env["ir.config_parameter"].set_param("argocd.simulate_commit", "False")

        with patch.multiple(
            "odoo.addons.argocd_deployer.models.application.Application",
            _get_deploy_content=mock_deploy_files,
            _get_repository=mock_get_repository,
        ):
            self.app.immediate_deploy()
            mock_get_repository.assert_called_once()
            mock_remote.pull.assert_called_once()
            mock_deploy_files.assert_called_once()
            mock_repository.commit.called_once_with(
                mock_repository, "Added `test-set`", ["application_set.yaml"]
            )
            mock_remote.push.assert_called_once()

    def test_immediate_destroy(self):
        mock_repository = MagicMock()
        mock_remote = MagicMock()
        mock_repository.remotes.origin = mock_remote
        mock_repository.working_dir = "/home/test"
        mock_get_repository = MagicMock(return_value=mock_repository)
        mock_destroy_files = MagicMock(
            return_value=({"remove": "test.yaml"}, "Removed `%s`.)")
        )

        # We're already patching here, so we don't have to simulate.
        simulate_commit = safe_eval(
            self.env["ir.config_parameter"].get_param("argocd.simulate_commit", False)
        )
        if simulate_commit:
            self.env["ir.config_parameter"].set_param("argocd.simulate_commit", "False")

        with patch.multiple(
            "odoo.addons.argocd_deployer.models.application.Application",
            _get_destroy_content=mock_destroy_files,
            _get_repository=mock_get_repository,
        ):
            self.app.immediate_destroy()
            mock_get_repository.assert_called_once()
            mock_remote.pull.assert_called_once()
            mock_destroy_files.assert_called_once()
            mock_repository.commit.called_once_with(
                mock_repository, "Removed `test-set`", ["application_set.yaml"]
            )
            mock_remote.push.assert_called_once()
