import os
from unittest.mock import MagicMock, mock_open, patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

APPLICATION_SET_PATCH = (
    "odoo.addons.argocd_deployer.models.application_set.ApplicationSet"
)


class TestApplicationSet(TransactionCase):
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
            }
        )

        cls.master_application_set = cls.env.ref("argocd_deployer.application_set_master")
        cls.default_application_set = cls.env.ref("argocd_deployer.application_set_default")
        cls.templated_yaml = f"""
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  repoURL: {cls.master_application_set.repository_url}
  revision: {cls.master_application_set.branch}
  path: {cls.master_application_set.deployment_directory}
  template-path: {{{{.path.path}}}}
"""

    def test_get_master_repository_directory(self):
        """The master repository directory is stored in the config.
        Check that it behaves."""
        master = self.env.ref("argocd_deployer.application_set_master")
        master.repository_directory = "/home/test"
        master.deployment_directory = "application_sets"
        with patch("os.makedirs") as mkdirs:
            self.application_set._get_master_repository_directory()
            mkdirs.assert_called_with("/home/test/main", mode=0o775)
        with self.assertRaisesRegex(UserError, "Master repository directory"):
            self.application_set._get_master_repository_directory("error")

    def test_master_deployment_directory(self):
        """The master deployment directory is the folder inside the master
        repository master application set lives. It's specified in the config."""
        master = self.env.ref("argocd_deployer.application_set_master")
        master.repository_directory = "/home/test"
        master.deployment_directory = "application_sets"
        with patch("os.makedirs") as mkdirs:
            self.env["argocd.application.set"]._get_master_deployment_directory()
            mkdirs.assert_called_with("/home/test/main/application_sets", mode=0o775)
        self.application_set.deployment_directory = "/this_directory_does_not_exist"
        with patch(
            f"{APPLICATION_SET_PATCH}._get_master_repository_directory",
            return_value="/home/test",
        ):
            with self.assertRaisesRegex(UserError, "Master deployment directory"):
                self.application_set._get_master_deployment_directory("error")

    def test_get_application_set_deployment_directory(self):
        """The application set deployment directory is folder inside the master
        repository where the application sets live. It's specified in the config."""

        with patch("os.makedirs") as mkdirs:
            self.application_set._get_application_set_deployment_directory()
            mkdirs.assert_called_with("/home/test/Olive/instances/test-set", mode=0o775)
        with patch(
            f"{APPLICATION_SET_PATCH}._get_application_set_repository_directory",
            return_value="/home/nonexistent/directory",
        ):
            with self.assertRaisesRegex(
                UserError, "Application set deployment directory"
            ):
                self.application_set._get_application_set_deployment_directory("error")

    def test_get_application_set_repository_directory(self):
        """The application set repository directory is stored in the application set.
        Check that it behaves."""
        with patch("os.makedirs") as mkdirs:
            self.application_set._get_application_set_repository_directory()
            mkdirs.assert_called_with("/home/test/Olive", mode=0o775)
        self.application_set.repository_directory = "/this_directory_does_not_exist/"
        with self.assertRaisesRegex(UserError, "Application set directory"):
            self.application_set._get_application_set_repository_directory("error")

    def test_get_application_deployment_directory(self):
        """The application deployment directory is a combination of the
        application repository directory and the deployment_directory in the
        application set."""
        with patch("os.makedirs") as mkdirs:
            self.application_set._get_application_deployment_directory("john")
            mkdirs.assert_called_with("/home/test/Olive/instances/john", mode=0o775)
        self.application_set.deployment_directory = "/this_directory_does_not_exist"
        with patch(
            f"{APPLICATION_SET_PATCH}._get_application_set_repository_directory",
            return_value="/home/test/Olive/test-set",
        ):
            with self.assertRaisesRegex(UserError, "Application deployment directory"):
                self.application_set._get_application_deployment_directory(
                    "john", "error"
                )

    def test_get_argocd_template(self):
        yaml = self.application_set._get_argocd_template()
        self.assertEqual(self.templated_yaml, yaml)

    def test_create_application_set(self):
        """Test that the application set is created correctly."""
        m = mock_open()
        with patch("builtins.open", m):
            with patch("os.makedirs") as mock_makedir:
                with patch("os.path.join", return_value="joined/path"):
                    files, message = self.application_set._create_application_set()
                    self.assertEqual(3, mock_makedir.call_count)
                    mock_makedir.assert_called_with("joined/path")
                    m.assert_called_once_with("joined/path", "w")
                    m().write.assert_called_once()
                    self.assertEqual({"add": ["joined/path"]}, files)
                    self.assertEqual("Added application set `%s`.", message)

    def test_remove_application_set(self):
        """Test that the application set is removed correct;=ly."""
        with patch("os.path.join", return_value="joined/path"):
            with patch("os.remove") as mock_remove:
                with patch("os.removedirs") as mock_removedirs:
                    with patch("os.path.exists", return_value=True):
                        files, message = self.application_set._remove_application_set()
                        mock_remove.assert_called_once_with("joined/path")
                        mock_removedirs.assert_called_once_with("joined/path")
                        self.assertEqual({"remove": ["joined/path"]}, files)
                        self.assertEqual("Removed application set `%s`.", message)

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
                    "callback": self.env.ref(
                        "argocd_deployer.application_set_master"
                    ).immediate_deploy,
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
                    "callback": self.env.ref(
                        "argocd_deployer.application_set_master"
                    ).immediate_destroy,
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
            "odoo.addons.argocd_deployer.models.application_set.ApplicationSet",
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
