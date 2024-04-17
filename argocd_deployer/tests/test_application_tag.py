from odoo import Command
from odoo.tests.common import TransactionCase


class TestApplicationTag(TransactionCase):
    def test_get_domain_yaml_path(self):
        """get_domain_yaml_path returns a reasonable value in all circumstances."""

        template = self.env["argocd.application.set.template"].create(
            {
                "name": "test-set-template",
                "yaml": """test:
  me: domain""",
            }
        )
        application_set_1 = self.env["argocd.application.set"].create(
            {
                "name": "test-set",
                "template_id": template.id,
                "repository_url": "http://hello.com",
                "branch": "hello",
                "repository_directory": "hello",
                "deployment_directory": "bye",
            }
        )
        application_set_2 = self.env["argocd.application.set"].create(
            {
                "name": "test-set-also",
                "template_id": template.id,
                "repository_url": "http://hello.com",
                "branch": "hello",
                "repository_directory": "hello",
                "deployment_directory": "byeagain",
            }
        )
        tag = self.env["argocd.application.tag"].create(
            {"name": "test-tag", "domain_yaml_path": False, "key": "thegoldentowerkey"}
        )

        self.assertFalse(tag.get_domain_yaml_path())
        self.assertFalse(tag.get_domain_yaml_path(application_set_1))

        tag.domain_yaml_path = "test.me"
        self.assertEqual("test.me", tag.get_domain_yaml_path())
        self.assertEqual("test.me", tag.get_domain_yaml_path(application_set_1))

        tag.domain_override_ids = [
            Command.create(
                {
                    "application_set_id": application_set_1.id,
                    "domain_yaml_path": "test.me.now",
                }
            )
        ]

        self.assertEqual("test.me", tag.get_domain_yaml_path())
        self.assertEqual("test.me.now", tag.get_domain_yaml_path(application_set_1))
        self.assertEqual("test.me", tag.get_domain_yaml_path(application_set_2))
