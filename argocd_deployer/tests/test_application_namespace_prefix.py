from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestApplicationNamespacePrefix(TransactionCase):
    def test_name(self):
        """Name may only contain lowercase letters, digits and underscores."""
        with self.assertRaisesRegex(
            ValidationError, "Only lowercase letters, numbers and dashes"
        ):
            self.env["argocd.application.namespace.prefix"].create({"name": "Hello"})

        with self.assertRaisesRegex(ValidationError, "max 100 characters"):
            self.env["argocd.application.namespace.prefix"].create(
                {
                    "name": "this-name-is-waaaaaaaaaaaaaaaaaaaaaaaaaaaaaaay-"
                    "toooooooooooooooooooooo-ridiculously-long-and should-"
                    "totally-not-be-allowed"
                }
            )

        self.env["argocd.application.namespace.prefix"].create(
            {"name": "hello-the-namespace"}
        )
