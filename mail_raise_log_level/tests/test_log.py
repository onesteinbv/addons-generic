from unittest.mock import patch

from odoo import modules

from odoo.addons.base.tests.common import BaseCommon


class TestLog(BaseCommon):
    def test_fetch_mail(self):
        # Create a broken fetchmail server
        self.env["fetchmail.server"].create(
            [
                {
                    "name": "Broken Server",
                    "server_type": "pop",
                    "server": "test",
                    "port": 110,
                    "user": "test",
                    "password": "test",
                    "state": "done",
                }
            ]
        )

        # Check if the log message was captured
        with self.assertLogs(
            "odoo.addons.mail_raise_log_level.models.fetch_mail_server", level="ERROR"
        ) as log:
            # Simulate cron
            self.env["fetchmail.server"]._fetch_mails()

            self.assertIn(
                "General failure when trying to fetch mail",
                log.records[0].message,
            )

    def test_failing_outgoing_mail(self):
        # Create a broken outgoing mail server
        mail_server = self.env["ir.mail_server"].create(
            [
                {
                    "name": "Broken Server",
                    "smtp_host": "test222",
                    "smtp_user": "test",
                    "smtp_pass": "test",
                    "smtp_port": 25,
                }
            ]
        )

        # Check if the log message was captured
        with self.assertLogs(
            "odoo.addons.mail_raise_log_level.models.mail_mail", level="ERROR"
        ) as log:
            mail = self.env["mail.mail"].create(
                [
                    {
                        "mail_server_id": mail_server.id,
                        "auto_delete": False,
                        "email_to": "test@123.com",
                        "email_from": "admin@123.com",
                        "subject": "Test",
                        "body_html": "<p>Test</p>",
                    }
                ]
            )
            with patch.object(modules.module, "current_test", False):
                mail.send()
                self.assertEqual(
                    mail.state,
                    "exception",
                )

                self.assertIn(
                    "Outgoing mail failure",
                    log.records[0].message,
                )
