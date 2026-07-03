from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

APPLICATION_SET_PATCH = (
    "odoo.addons.argocd_deployer.models.application_set.ApplicationSet"
)


class TestApplicationSet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.application_set = cls.env["argocd.application.set"].create(
            {
                "name": "test-set",
                "repository_url": "git@github.com:odoo/odoo.git",
                "branch": "Olive",
                "repository_directory": "/home/test",
                "deployment_directory": "instances",
                "namespace_prefix": "app-",
            }
        )

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
