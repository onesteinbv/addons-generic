from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestApplicationDomain(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        application_set_id = cls.env.ref("argocd_deployer.application_set_default").id
        app_template_id = cls.env.ref(
            "argocd_deployer.demo_curq_basis_application_template"
        ).id
        cls.app_1 = cls.env["argocd.application"].create(
            {
                "name": "myapp",
                "template_id": app_template_id,
                "application_set_id": application_set_id,
            }
        )
        cls.app_2 = cls.env["argocd.application"].create(
            {
                "name": "myapp2",
                "template_id": app_template_id,
                "application_set_id": application_set_id,
            }
        )

    def test_uniqueness(self):
        argocd_application_domain = self.env["argocd.application.domain"]
        global_domain = argocd_application_domain.create(
            {"application_id": self.app_1.id, "name": "mydomain", "scope": "odoo"}
        )
        with self.subTest("Record should not constrain itself"):
            global_domain.write({"name": "mydomain", "scope": "odoo1"})
            global_domain.name = "mydomain"
            global_domain.write({"name": "mydomain3", "scope": "odoo1"})
            global_domain.name = "mydomain"

        argocd_application_domain.create(
            {"application_id": self.app_2.id, "name": "mydomain2", "scope": "odoo"}
        )
        with self.assertRaisesRegex(ValidationError, "already in use"):
            argocd_application_domain.create(
                {"application_id": self.app_1.id, "name": "mydomain2", "scope": "nc"}
            )
        with self.assertRaisesRegex(ValidationError, "already in use"):
            global_domain.write({"name": "mydomain2"})
        with self.assertRaisesRegex(ValidationError, "already in use"):
            global_domain.name = "mydomain2"

        scope_unique_domain = argocd_application_domain.create(
            {
                "application_id": self.app_1.id,
                "name": "scoped-domain",
                "scope": "mail",
                "scope_unique": True,
            }
        )
        with self.subTest(
            "'scoped-domain' should be available in global and other scope"
        ):
            argocd_application_domain.create(
                {
                    "application_id": self.app_2.id,
                    "name": "scoped-domain",
                    "scope": "odoo",
                }
            )
            argocd_application_domain.create(
                {
                    "application_id": self.app_2.id,
                    "name": "scoped-domain",
                    "scope": "other scope",
                    "scope_unique": True,
                }
            )
        with self.assertRaisesRegex(ValidationError, "already in use"):
            argocd_application_domain.create(
                {
                    "application_id": self.app_2.id,
                    "name": "scoped-domain",
                    "scope": "mail",
                    "scope_unique": True,
                }
            )
        with self.assertRaisesRegex(ValidationError, "already in use"):
            scope_unique_domain.scope = "other scope"
        with self.assertRaisesRegex(ValidationError, "already in use"):
            scope_unique_domain.scope_unique = False
        with self.assertRaisesRegex(ValidationError, "already in use"):
            scope_unique_domain.write({"scope_unique": False})

    def test_create_domain(self):
        argocd_application_domain = self.env["argocd.application.domain"]
        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="odoo"
        )
        self.assertEqual(domain, "myapp")
        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="odoo"
        )
        self.assertEqual(domain, "myapp", "Domain should be unchanged")
        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="nc"
        )
        self.assertEqual(
            domain,
            "myapp1",
            "Same application but different scope should make unique domain",
        )

        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="nc"
        )
        self.assertEqual(domain, "myapp2")
        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", "customerx", scope="otherscope"
        )
        self.assertEqual(domain, "customerx", "Alternative should have been used")
        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", "customerx", "another", scope="anotherscope"
        )
        self.assertEqual(domain, "another", "Second alternative should have been used")

        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="mail", scope_unique=True
        )
        self.assertEqual(domain, "myapp")
        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="mail", scope_unique=True
        )
        self.assertEqual(domain, "myapp", "Domain should be unchanged")

        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="mail", scope_unique=True
        )
        self.assertEqual(domain, "myapp1")
        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="mail", scope_unique=True
        )
        self.assertEqual(domain, "myapp1", "Domain should be unchanged")

        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="scoped_domain", scope_unique=True
        )
        self.assertEqual(
            domain,
            "myapp",
            "Scope unique domain should still be available in different scope",
        )
