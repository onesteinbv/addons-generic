from odoo import Command
from odoo.tests.common import TransactionCase


class AccountGroupTest(TransactionCase):
    def test_allowed_journals(self):
        """Test wheter the account_ids field is correctly computed"""
        allowed_journals = self.env["account.journal"].create(
            {
                "code": "j1",
                "type": "bank",
                "name": "Journal 1",
            }
        )
        # Create a account group
        group = self.env["account.group"].create(
            {
                "name": "Test Group",
                "code_prefix_start": "1000",
                "code_prefix_end": "1999",
                "allowed_journal_ids": [Command.set(allowed_journals.ids)],
                "auto_allowed_journals": False,
            }
        )
        # Create a test account
        account = self.env["account.account"].create(
            {
                "code": "1000",
                "name": "Test Account",
                "group_id": group.id,
            }
        )
        self.assertEqual(group.id, account.group_id.id)

        self.assertNotIn(
            allowed_journals.id,
            account.allowed_journal_ids.ids,
            "The account should not have the allowed journals.",
        )

        # Enable auto_allowed_journals
        group.auto_allowed_journals = True
        self.assertIn(
            allowed_journals.id,
            account.allowed_journal_ids.ids,
            "The account should have the allowed journals after enabling auto allowed journals.",
        )

        # Add a new journal to the group we expect it to be added to the account
        new_allowed_journal = self.env["account.journal"].create(
            {"code": "j2", "type": "bank", "name": "Journal 2"}
        )
        group.allowed_journal_ids = [Command.link(new_allowed_journal.id)]
        self.assertIn(
            new_allowed_journal.id,
            account.allowed_journal_ids.ids,
            "The account should have the allowed journals after enabling auto allowed journals.",
        )

    def test_active_allowed_journals(self):
        """Test active_allowed_journal_ids specifically the inverse and recursive compute methods"""
        # Create a test company
        company = self.env["res.company"].create(
            {"name": "Test Company", "chart_template": "nl_rgs"}
        )
        parent_journals = self.env["account.journal"].create(
            {
                "code": "j1",
                "type": "bank",
                "name": "Journal 1",
                "company_id": company.id,
            }
        )
        child_journals = self.env["account.journal"].create(
            {
                "code": "j2",
                "type": "bank",
                "name": "Journal 2",
                "company_id": company.id,
            }
        )
        grandchild_journals = self.env["account.journal"].create(
            {
                "code": "j3",
                "type": "bank",
                "name": "Journal 3",
                "company_id": company.id,
            }
        )
        # Create a account group with allowed journals
        group1 = self.env["account.group"].create(
            {
                "name": "Test Group 1",
                "company_id": company.id,
                "allowed_journal_ids": [Command.set(parent_journals.ids)],
            }
        )

        # Create a child group with allowed journals
        group2 = self.env["account.group"].create(
            {
                "name": "Test Group 2",
                "company_id": company.id,
                "parent_id": group1.id,
                "allowed_journal_ids": [Command.set(child_journals.ids)],
            }
        )
        group3 = self.env["account.group"].create(
            {
                "name": "Test Group 3",
                "company_id": company.id,
                "parent_id": group2.id,
                "allowed_journal_ids": [Command.set(grandchild_journals.ids)],
            }
        )
        # Check the active_allowed_journal_ids for the child group adn grandchild group
        self.assertEqual(
            set(group2.active_allowed_journal_ids.ids),
            set(parent_journals.ids + child_journals.ids),
            "The active_allowed_journal_ids for the child group should include the parent group's allowed journals.",
        )
        self.assertEqual(
            set(group3.active_allowed_journal_ids.ids),
            set(parent_journals.ids + child_journals.ids + grandchild_journals.ids),
            "The active_allowed_journal_ids for the grandchild group should include the parent group's allowed journals.",
        )
