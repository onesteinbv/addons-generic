from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.membership_activity_gitlab.models.project_project import use_gitlab
from odoo.addons.queue_job.exception import RetryableJobError

from gitlab import GitlabError


class TestGitlab(TransactionCase):
    def test_retryable_error_on_502(self):
        """Test that a RetryableJobError is raised when a 502 error occurs."""

        # Mock get_gitlab_commits_iterated to raise a GitlabError with a 502 response code
        project = self.env["project.project"].create(
            {
                "name": "Test Project",
                "gitlab_id": self.env["gitlab"]
                .create(
                    {
                        "url": "https://gitlab.com",
                        "private_token": "fake_token",
                    }
                )
                .id,
            }
        )

        @use_gitlab
        def mock_get_gitlab_commits_iterated(self, page, per_page, since, until):
            raise GitlabError("Bad Gateway", response_code=502)

        with patch(
            "odoo.addons.membership_activity_gitlab.models."
            "project_project.Project.get_gitlab_commits_iterated",
            new=mock_get_gitlab_commits_iterated,
        ):
            with self.assertRaises(RetryableJobError):
                project.get_gitlab_commits_iterated(1, 100, "2024-01-01", "2024-01-31")
