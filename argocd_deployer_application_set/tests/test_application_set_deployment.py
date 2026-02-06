from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase


class TestApplicationSetDeployment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.application_set_template = cls.env[
            "argocd.application.set.template"
        ].create(
            {
                "name": "test-template",
                "yaml": """
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  repoURL: {{.config.repository_url}}
  revision: {{.config.branch}}
  path: {{.config.deployment_directory}}
  template-path: {{.path.path}}
  destination:
    namespace: {{.application_set.namespace_prefix}}{{.path.basename}}
""",
            }
        )
        cls.application_set = cls.env["argocd.application.set"].create(
            {
                "name": "test-set",
                "repository_url": "git@github.com:odoo/odoo.git",
                "branch": "Olive",
                "template_id": cls.application_set_template.id,
                "repository_directory": "/home/test",
                "deployment_directory": "instances",
                "namespace_prefix": "app-",
            }
        )

        cls.master_application_set = cls.env.ref(
            "argocd_deployer.application_set_master"
        )

    def _disable_simulation(self):
        simulation_mode = (
            self.env["ir.config_parameter"]
            .get_param("argocd.git_simulation_mode", "none")
            .lower()
        )
        if simulation_mode != "none":
            self.env["ir.config_parameter"].set_param(
                "argocd.git_simulation_mode", "none"
            )

    def test_deploy_and_destroy(self):
        """Test deployment and destruction of application sets"""
        mock_repository = MagicMock()
        mock_remote = MagicMock()
        mock_get_repository = MagicMock()
        mock_change_files = MagicMock()
        self._disable_simulation()  # We're patching instead

        def reset_mocks(instruction, message):
            """Reset the mocks so they can be reused again"""
            mock_repository.reset_mock()
            mock_remote.reset_mock()
            mock_get_repository.reset_mock()
            mock_change_files.reset_mock()
            mock_repository.remotes.origin = mock_remote
            mock_repository.working_dir = "/home/test"
            mock_get_repository.return_value = mock_repository
            mock_change_files.return_value = instruction, message

        test_cases = [
            {
                "name": "Deploy master set",
                "fixture": {
                    "callback": self.master_application_set.immediate_deploy,
                    "instruction": {"add": "application_set.yaml"},
                    "message": "Added `%s`",
                },
                "expected": {
                    "message": "Added `test-set`",
                    "files": ["application_set.yaml"],
                },
            },
            {
                "name": "Deploy application set",
                "fixture": {
                    "callback": self.application_set.immediate_deploy,
                    "instruction": {"add": "application_set.yaml"},
                    "message": "Added `%s`",
                },
                "expected": {
                    "message": "Added `test-set`",
                    "files": ["application_set.yaml"],
                },
            },
            {
                "name": "Destroy master set",
                "fixture": {
                    "callback": self.master_application_set.immediate_destroy,
                    "instruction": {"remove": "application_set.yaml"},
                    "message": "Removed `%s`",
                },
                "expected": {
                    "message": "Removed `test-set`",
                    "files": ["application_set.yaml"],
                },
            },
            {
                "name": "Destroy application set",
                "fixture": {
                    "callback": self.application_set.immediate_destroy,
                    "instruction": {"remove": "application_set.yaml"},
                    "message": "Removed `%s`",
                },
                "expected": {
                    "message": "Removed `test-set`",
                    "files": ["application_set.yaml"],
                },
            },
        ]

        with patch.multiple(
            "odoo.addons.argocd_deployer_application_set.models.application_set.ApplicationSet",
            _create_master_application_set=mock_change_files,
            _create_application_set=mock_change_files,
            _remove_master_application_set=mock_change_files,
            _remove_application_set=mock_change_files,
            _get_repository=mock_get_repository,
        ):
            for test_case in test_cases:
                with self.subTest(msg=test_case["name"]):
                    self.env.cr.execute("SAVEPOINT test_deploy;")
                    reset_mocks(
                        test_case["fixture"]["instruction"],
                        test_case["fixture"]["message"],
                    )
                    test_case["fixture"]["callback"]()
                    mock_get_repository.assert_called_once()
                    mock_remote.pull.assert_called_once()
                    mock_change_files.assert_called_once()
                    mock_repository.commit.called_once_with(
                        mock_repository,
                        test_case["expected"]["files"],
                        test_case["expected"]["message"],
                    )
                    mock_remote.push.assert_called_once()
                    self.env.cr.execute("ROLLBACK TO test_deploy;")

    def test_render_config(self):
        """Test that render_config properly generates the YAML configuration"""
        self.application_set.render_config()
        self.assertIn("Olive", self.application_set.config)
        self.assertIn("app-", self.application_set.config)
