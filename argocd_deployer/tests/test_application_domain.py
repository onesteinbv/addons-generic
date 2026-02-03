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
        scope = self.env["argocd.application.domain.scope"].create({"name": "app"})
        scope_2 = self.env["argocd.application.domain.scope"].create({"name": "mail"})
        global_domain = argocd_application_domain.create(
            {"application_id": self.app_1.id, "name": "mydomain", "scope_id": scope.id}
        )
        with self.subTest("Record should not constrain itself"):
            global_domain.write({"name": "mydomain", "scope_id": scope.id})
            global_domain.name = "mydomain"
            global_domain.write({"name": "mydomain3", "scope_id": scope.id})
            global_domain.name = "mydomain3"

        argocd_application_domain.create(
            {
                "application_id": self.app_2.id,
                "name": "mydomain2",
                "scope_id": scope_2.id,
            }
        )
        with self.assertRaisesRegex(ValidationError, "already in use"):
            argocd_application_domain.create(
                {
                    "application_id": self.app_1.id,
                    "name": "mydomain2",
                    "scope_id": scope_2.id,
                }
            )
        with self.assertRaisesRegex(ValidationError, "already in use"):
            global_domain.write({"name": "mydomain2", "scope_id": scope_2.id})
        with self.assertRaisesRegex(ValidationError, "already in use"):
            global_domain.name = "mydomain2"

    def test_create_domain(self):
        argocd_application_domain = self.env["argocd.application.domain"]
        argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="dn", scope_unique=True
        )
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
            self.app_1, "myapp", scope="mail"
        )
        self.assertEqual(domain, "myapp")
        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp", scope="mail"
        )
        self.assertEqual(domain, "myapp", "Domain should be unchanged")

        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="mail"
        )
        self.assertEqual(domain, "myapp1")
        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="mail"
        )
        self.assertEqual(domain, "myapp1", "Domain should be unchanged")

        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp", scope="scoped_domain"
        )
        self.assertEqual(
            domain,
            "myapp",
            "Scope unique domain should still be available in different scope",
        )

    def test_subdomain(self):
        argocd_application_domain = self.env["argocd.application.domain"]
        domain = argocd_application_domain.create_domain(
            self.app_2, "myapp.saas.com", scope="website"
        )
        self.assertEqual(domain, "myapp.saas.com")
        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp.saas.com", scope="website"
        )
        self.assertEqual(domain, "myapp1.saas.com", "it should change the subdomain")

        domain = argocd_application_domain.create_domain(
            self.app_1, "myapp.saas.com", scope="matomo"
        )
        self.assertEqual(domain, "myapp2.saas.com", "it should change the subdomain")

        domain = argocd_application_domain.create_domain(
            self.app_1, "nosub", scope="haystack"
        )
        self.assertEqual(domain, "nosub")

        domain = argocd_application_domain.create_domain(
            self.app_2, "nosub", scope="haystack"
        )
        self.assertEqual(domain, "nosub1")
