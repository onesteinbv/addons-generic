import re
from datetime import datetime
from functools import wraps
from math import ceil

from github import Auth, Github
from github.GithubException import RateLimitExceededException

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.queue_job.exception import RetryableJobError


def use_github(method):
    @wraps(method)
    def _wrap(self, *args, **kwargs):
        self.ensure_one()
        if not self.github_full_name:
            raise UserError(_("Github Fullname is not set."))
        current_timestamp = int(datetime.timestamp(datetime.now()))
        if (
            self.github_rate_limiting_resettime
            and current_timestamp < self.github_rate_limiting_resettime
        ):
            raise RetryableJobError(
                "API Rate limit reached",
                seconds=self.github_rate_limiting_resettime - current_timestamp,
            )
        elif self.github_rate_limiting_resettime:
            self.github_rate_limiting_resettime = 0

        try:
            hub = self._create_github_instance()
            return method(self, *args, **kwargs)
        except RateLimitExceededException as e:
            self.env.cr.rollback()
            # rate_limiting_resettime property will do a http request so store it
            self.github_rate_limiting_resettime = hub.rate_limiting_resettime
            # FIXME: Is there not a better pattern we can use here?
            self.env.cr.commit()  # pylint: disable=invalid-commit
            raise RetryableJobError(
                e.data["message"],
                seconds=hub.rate_limiting_resettime - current_timestamp,
            ) from e

    return _wrap


class Project(models.Model):
    _inherit = "project.project"

    github_full_name = fields.Char(
        string="Github Fullname",
        help="e.g. 'odoo/odoo' (for https://github.com/odoo/odoo)",
    )
    github_rate_limiting_resettime = fields.Integer()

    @api.constrains("github_full_name")
    def _constrain_github_full_name(self):
        for project in self.filtered(lambda p: p.github_full_name):
            if not re.match(r"[\w\-]+/[\w\-]+", project.github_full_name):
                raise ValidationError(
                    _(
                        "Please enter a valid full name e.g. odoo/odoo (for https://github.com/odoo/odoo)"
                    )
                )

    @api.model
    def _create_github_instance(self):
        config_sudo = self.env["ir.config_parameter"].sudo()
        access_token = config_sudo.get_param("membership_activity_github.access_token")
        if not access_token:
            raise UserError(
                _(
                    "Please configure `membership_activity_github.access_token` system parameter."
                )
            )
        auth = Auth.Token(access_token)
        return Github(auth=auth)

    @api.model
    def _get_github_batch_size(self):
        """Batch size in pages"""
        config_sudo = self.env["ir.config_parameter"].sudo()
        batch_size = config_sudo.get_param("membership_activity_github.batch_size", "3")
        return int(batch_size)

    def get_github_commits(self):
        batch_size = self._get_github_batch_size()
        hub = self._create_github_instance()
        until = fields.Datetime.now()
        for project in self:
            since = project.get_last_membership_activity_date_by_type(
                "membership_activity_cde.commit"
            )  # Get since for every project separately to prevent errors due to the batching and delaying
            repo = hub.get_repo(project.github_full_name)
            params = {"until": until}
            if since:
                params.update(since=since)
            commits = repo.get_commits(**params)
            commit_count = commits.totalCount
            pages = range(0, ceil(commit_count / hub.per_page), batch_size)
            for page in pages:
                project.with_delay(max_retries=0).get_github_commits_immediately(
                    page, page + batch_size, since, until
                )

    @use_github
    def get_github_commits_immediately(self, start_page, end_page, since, until):
        self.ensure_one()
        hub = self._create_github_instance()
        params = {"since": since, "until": until}
        activity_type = self.env.ref("membership_activity_cde.commit")
        repo = hub.get_repo(self.github_full_name)
        commits = repo.get_commits(**params)
        vals_list = []
        for page in range(start_page, end_page):
            for commit in commits.get_page(page):
                author_still_exists = commit.raw_data["author"]
                login = author_still_exists and commit.author.login
                if not login:
                    login = commit.commit.author.name
                vals_list.append(
                    {
                        "project_id": self.id,
                        "github_login": login,
                        "type_id": activity_type.id,
                        "url": commit.html_url,
                        "date": commit.commit.author.date,
                    }
                )

        self.env["membership.activity"].create(vals_list)

    def get_github_issues(self):
        batch_size = self._get_github_batch_size()
        hub = self._create_github_instance()
        for project in self:
            repo = hub.get_repo(project.github_full_name)
            # Issues get updated when they have a new review
            since = min(
                project.get_last_membership_activity_date_by_type(
                    "membership_activity_cde.issue"
                ),
                project.get_last_membership_activity_date_by_type(
                    "membership_activity_cde.pr"
                ),
            )
            params = {"sort": "created", "direction": "asc", "since": since}

            issues = repo.get_issues(**params)
            count = issues.totalCount
            pages = range(0, ceil(count / hub.per_page), batch_size)
            for page in pages:
                project.with_delay(max_retries=0).get_github_issues_immediately(
                    page, page + batch_size, since
                )

    @use_github
    def get_github_issues_immediately(self, start_page, end_page, since):
        self.ensure_one()
        hub = self._create_github_instance()
        params = {"sort": "created", "direction": "asc", "since": since}
        activity_type_issue = self.env.ref("membership_activity_cde.issue")
        activity_type_pr = self.env.ref("membership_activity_cde.pr")
        activity_type_review = self.env.ref("membership_activity_cde.review")
        repo = hub.get_repo(self.github_full_name)
        issues = repo.get_issues(**params)
        vals_list = []
        for page in range(start_page, end_page):
            for issue in issues.get_page(page):
                exists = self.env["membership.activity"].search(
                    [("url", "=", issue.html_url), ("project_id", "=", self.id)],
                    count=True,
                )
                if not exists:
                    type_id = (
                        issue.pull_request
                        and activity_type_pr.id
                        or activity_type_issue.id
                    )
                    vals_list.append(
                        {
                            "project_id": self.id,
                            "github_login": issue.user and issue.user.login,
                            "type_id": type_id,
                            "date": issue.created_at,
                            "url": issue.html_url,
                        }
                    )

                if issue.pull_request:
                    pull = repo.get_pull(issue.number)
                    reviews = pull.get_reviews()
                    for review in reviews:
                        review_exists = self.env["membership.activity"].search(
                            [
                                (
                                    "project_id",
                                    "=",
                                    self.id,
                                ),  # This leaf is not really required
                                ("url", "=", review.html_url),
                            ],
                            count=True,
                        )
                        if not review_exists:
                            vals_list.append(
                                {
                                    "project_id": self.id,
                                    "github_login": review.user and review.user.login,
                                    "type_id": activity_type_review.id,
                                    "date": review.submitted_at,
                                    "url": review.html_url,
                                }
                            )
        self.env["membership.activity"].create(vals_list)

    def get_github_comments(self):
        batch_size = self._get_github_batch_size()
        hub = self._create_github_instance()
        for project in self:
            repo = hub.get_repo(project.github_full_name)
            since = project.get_last_membership_activity_date_by_type(
                "membership_activity_cde.comment"
            )
            params = {"sort": "created", "direction": "asc", "since": since}

            # Get comments on issues and pull requests
            # Every pull request is an issue, but not every issue is a pull request
            comments = repo.get_issues_comments(**params)
            count = comments.totalCount
            pages = range(0, ceil(count / hub.per_page), batch_size)
            for page in pages:
                project.with_delay(max_retries=0).get_github_comments_immediately(
                    page, page + batch_size, since
                )

    @use_github
    def get_github_comments_immediately(self, start_page, end_page, since):
        self.ensure_one()
        hub = self._create_github_instance()
        params = {"sort": "created", "direction": "asc", "since": since}
        activity_type = self.env.ref("membership_activity_cde.comment")
        repo = hub.get_repo(self.github_full_name)
        comments = repo.get_issues_comments(**params)
        vals_list = []
        for page in range(start_page, end_page):
            for comment in comments.get_page(page):
                comment_exists = self.env["membership.activity"].search(
                    [("project_id", "=", self.id), ("url", "=", comment.html_url)],
                    count=True,
                )
                if comment_exists:
                    continue
                vals_list.append(
                    {
                        "project_id": self.id,
                        "github_login": comment.user and comment.user.login,
                        "type_id": activity_type.id,
                        "date": comment.created_at,
                        "url": comment.html_url,
                    }
                )
        self.env["membership.activity"].create(vals_list)

    @api.model
    def cron_import_github_activity(self):
        projects = self.search([("github_full_name", "!=", False)])
        projects.get_github_commits()
        projects.get_github_issues()
        projects.get_github_comments()
