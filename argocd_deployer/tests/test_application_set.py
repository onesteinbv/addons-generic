from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestApplicationSet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.application_set = cls.env["argocd.application.set"].create(
            {
                "name": "Test Set",
                "repository_url": "git@github.com:odoo/odoo.git",
                "branch": "Olive",
                "repository_directory": "/home/test",
                "instances_directory": "instances",
            }
        )

    def test_get_repository_directory(self):
        with patch("os.makedirs") as mkdirs:
            self.application_set._get_repository_directory()
            mkdirs.assert_called_with("/home/test", mode=0o775)
        self.application_set.repository_directory = "/this_directory_does_not_exist/"
        with self.assertRaisesRegex(UserError, "Repository directory"):
            self.application_set._get_repository_directory(False)

    def test_get_instances_directory(self):
        with patch("os.makedirs") as mkdirs:
            self.application_set._get_instances_directory()
            mkdirs.assert_called_with("/home/test/instances", mode=0o775)
        self.application_set.repository_directory = "/this_directory_does_not_exist/"
        with self.assertRaisesRegex(UserError, "Instances directory"):
            self.application_set._get_instances_directory(False)
