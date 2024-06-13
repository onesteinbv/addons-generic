import os
import re

from git import Repo

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from .repository_base import ADD_FILES, REMOVE_FILES


class ApplicationSet(models.Model):
    _name = "argocd.application.set"
    _description = "ArgoCD Application Set"
    _inherit = ["mail.thread", "argocd.repository.base"]
    _order = "name asc"
    _rec_name = "description"

    name = fields.Char(required=True, index=True)
    description = fields.Char()
    template_id = fields.Many2one("argocd.application.set.template", required=True)
    is_deployed = fields.Boolean(compute="_compute_is_deployed")
    has_deployed_applications = fields.Boolean(
        compute="_compute_has_deployed_applications"
    )
    repository_url = fields.Char(
        required=True, help="URL of the repository that is updated by the applications."
    )
    branch = fields.Char(
        required=True,
        default="master",
        help="The branch on the repository that will be used for deployments in this application set.",
    )
    repository_directory = fields.Char(
        required=True, help="Local path in which to store the application repository."
    )
    deployment_directory = fields.Char(
        help="Folder inside the repository in which to store the application YAML files.",
    )
    domain_format = fields.Char(
        required=True,
        help="The domain format used to build the domain for the deployment.",
        default="-",
    )
    subdomain_format = fields.Char(
        required=True,
        help="The domain format used to build the domain for the deployment.",
        default="-",
    )
    namespace_prefix_id = fields.Many2one("argocd.application.namespace.prefix")

    _sql_constraints = [
        ("application_set_name_unique", "unique(name)", "Already exists"),
        (
            "app_set_unique",
            "unique(repository_url, branch, deployment_directory)",
            "Another app set is already linked to this repository, branch and instances folder.",
        ),
    ]
    is_master = fields.Boolean(
        default=False,
        compute="_compute_is_master",
        store=True,
        help="Indicates that this is the master application set. "
        "This set must be manually installed in ArgoCD. "
        "Application sets deployed in CURQ are deployed in "
        "the master set.",
    )
    is_destroying = fields.Boolean(compute="_compute_is_destroying")
    application_ids = fields.One2many(
        "argocd.application", inverse_name="application_set_id"
    )
    master_application_set_id = fields.Many2one(comodel_name="argocd.application.set")

    @api.constrains("repository_directory")
    def _check_unique_repository_directory(self):
        if not self.is_master:
            return
        other_masters = (
            self.env["argocd.application.set"].search(
                [
                    ("is_master", "=", True),
                    ("repository_directory", "=", self.repository_directory),
                ]
            )
            - self
        )
        if other_masters:
            raise ValidationError(
                "Master application set with the same `Repository Directory` exists."
            )

    @api.depends("master_application_set_id")
    def _compute_is_master(self):
        for app_set in self:
            app_set.is_master = not bool(app_set.master_application_set_id)

    @api.constrains("deployment_directory")
    def _check_deployment_directory(self):
        if not self.deployment_directory:
            raise ValidationError("Deployment directory is required.")
        if self.deployment_directory[-1] == "/":
            raise ValidationError("Deployment directories should not end with '/'.")

    @api.constrains("name")
    def _constrain_name(self):
        if not re.match(
            "^[a-z0-9-]{1,100}$", self.name
        ):  # lowercase a to z, 0 to 9 and - (dash) are allowed
            raise ValidationError(
                _(
                    "Only lowercase letters, numbers and dashes are allowed in the "
                    "name (max 100 characters)."
                )
            )

    @staticmethod
    def _create_path_or_error(path, directory_name, path_does_not_exist_action):
        if not os.path.exists(path):
            if path_does_not_exist_action == "error":
                raise UserError(f"{directory_name} ({path}) doesn't exist.")
            elif path_does_not_exist_action == "create":
                os.makedirs(path, mode=0o775)
            elif path_does_not_exist_action == "ignore":
                pass
            else:
                raise NotImplementedError("Path does not exist.")

    def _get_master_repository_directory(self, path_does_not_exist_action="create"):
        self.ensure_one()
        master = self.master_application_set_id or self
        path = os.path.join(
            master.repository_directory,
            master.branch,
        )
        self._create_path_or_error(
            path, "Master repository directory", path_does_not_exist_action
        )
        return path

    def _get_master_deployment_directory(self, path_does_not_exist_action="create"):
        """Return the directory the master application set lives."""
        self.ensure_one()
        master = self.master_application_set_id or self
        path = os.path.join(
            self._get_master_repository_directory(path_does_not_exist_action),
            master.deployment_directory,
        )
        self._create_path_or_error(
            path, "Master deployment directory", path_does_not_exist_action
        )
        return path

    def _get_application_set_repository_directory(
        self, path_does_not_exist_action="create"
    ):
        """Return the directory in which the applications in the current application
        set are located."""
        self.ensure_one()
        path = os.path.join(
            self.repository_directory,
            self.branch,
        )
        self._create_path_or_error(
            path, "Application set directory", path_does_not_exist_action
        )
        return path

    def _get_application_set_deployment_directory(
        self, path_does_not_exist_action="create"
    ):
        """Return the directory in which all application sets live."""
        self.ensure_one()
        path = os.path.join(
            self._get_master_deployment_directory(path_does_not_exist_action),
            self.name,
        )
        self._create_path_or_error(
            path, "Application set deployment directory", path_does_not_exist_action
        )
        return path

    def _get_application_deployment_directory(
        self, application_name, path_does_not_exist_action="create"
    ):
        self.ensure_one()
        path = os.path.join(
            self._get_application_set_repository_directory(path_does_not_exist_action),
            self.deployment_directory,
            application_name,
        )
        self._create_path_or_error(
            path, "Application deployment directory", path_does_not_exist_action
        )
        return path

    def _compute_is_deployed(self):
        for app_set in self:
            if app_set.is_master:
                path = app_set._get_master_repository_directory("ignore")
                path = os.path.join(path, "master_application_set/templates")
            else:
                path = app_set._get_application_set_deployment_directory("ignore")
            path = os.path.join(
                path,
                "application_set.yaml",
            )
            app_set.is_deployed = os.path.isfile(path)

    def _find_destroy_queue_jobs(self):
        self.ensure_one()
        return (
            self.env["queue.job"]
            .search(
                [
                    ("model_name", "=", "argocd.application.set"),
                    ("state", "=", "pending"),
                    ("method_name", "=", "immediate_destroy"),
                ]
            )
            .filtered(lambda job: self.id in job.records.ids)
        )

    def _compute_is_destroying(self):
        for app_set in self:
            jobs = app_set._find_destroy_queue_jobs()
            app_set.is_destroying = bool(jobs)

    @api.depends("application_ids")
    def _compute_has_deployed_applications(self):
        for app_set in self:
            app_set.has_deployed_applications = app_set.application_ids.filtered(
                lambda a: a.is_deployed
            )

    def _get_master_repository(self):
        """Get the repository that contains the application sets."""
        directory = self._get_master_repository_directory("create")
        if os.path.exists(os.path.join(directory, ".git")):
            return Repo.init(directory)
        else:
            return Repo.clone_from(self.repository_url, directory)

    def _get_repository(self):
        """Get the repository specified in the application set."""
        directory = self._get_master_repository_directory("create")
        if os.path.exists(os.path.join(directory, ".git")):
            return Repo.init(directory)
        else:
            return Repo.clone_from(self.repository_url, directory)

    def _get_branch(self):
        return self.master_application_set_id.branch or self.branch

    def _format_commit_message(self, message):
        return message % self.name

    def _get_argocd_template(self):
        self.ensure_one()
        master = self.master_application_set_id or self
        replacements = {
            "{{.config.repository_url}}": master.repository_url or "" or "",
            "{{.config.branch}}": master.branch or "main",
            "{{.config.deployment_directory}}": (
                master.deployment_directory or "application_sets"
            ),
            "{{.application_set.name}}": self.name or "",
            "{{.application_set.repository_url}}": self.repository_url or "",
            "{{.application_set.branch}}": self.branch or "",
            "{{.application_set.deployment_directory}}": self.deployment_directory
            or "",
            "{{.application_set.namespace_prefix}}": self.namespace_prefix_id.name
            or "",
        }
        template_yaml = self.template_id.yaml
        for key, value in replacements.items():
            template_yaml = template_yaml.replace(key, value)
        return template_yaml

    def _create_master_application_set(self):
        """The master application set will be deployed in a master_application_set folder
        in the root of the repository. There will be a templates folder in it, and a
        Chart.yaml file."""
        self.ensure_one()
        template_yaml = self._get_argocd_template()
        repo_dir = self._get_master_repository_directory("create")
        application_set_dir = os.path.join(repo_dir, "master_application_set")
        template_dir = os.path.join(application_set_dir, "templates")
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        message = "Added application set `%s`."

        yaml_file = os.path.join(template_dir, "application_set.yaml")
        with open(yaml_file, "w") as fh:
            fh.write(template_yaml)

        chart_file = os.path.join(application_set_dir, "Chart.yaml")
        with open(chart_file, "w") as fh:
            fh.write(
                f"""apiVersion: v2
name: application-set-{self.name}
version: 1.0.0
appVersion: "1.0.0"
"""
            )
        return {ADD_FILES: [yaml_file, chart_file]}, message

    def _create_application_set(self):
        """Deploy a new application set for ArgoCD."""
        self.ensure_one()
        template_yaml = self._get_argocd_template()
        deployment_directory = self._get_application_set_deployment_directory("create")
        if not os.path.exists(deployment_directory):
            os.makedirs(deployment_directory)

        yaml_file = os.path.join(deployment_directory, "application_set.yaml")
        message = "Added application set `%s`."
        with open(yaml_file, "w") as fh:
            fh.write(template_yaml)

        return {ADD_FILES: [yaml_file]}, message

    def _remove_master_application_set(self):
        """Remove an application set for ArgoCD."""
        self.ensure_one()
        repo_dir = self._get_master_repository_directory("error")
        application_set_dir = os.path.join(repo_dir, "master_application_set")
        template_dir = os.path.join(application_set_dir, "templates")
        message = "Removed application set `%s`."
        yaml_file = os.path.join(template_dir, "application_set.yaml")
        chart_file = os.path.join(application_set_dir, "Chart.yaml")
        os.remove(chart_file)
        os.remove(yaml_file)
        os.removedirs(template_dir)

        return {REMOVE_FILES: [yaml_file, chart_file]}, message

    def _remove_application_set(self):
        """Remove an application set for ArgoCD."""
        self.ensure_one()
        deployment_directory = self._get_application_set_deployment_directory("error")
        message = "Removed application set `%s`."
        yaml_file = os.path.join(deployment_directory, "application_set.yaml")
        os.remove(yaml_file)
        if not self.is_master:
            os.removedirs(deployment_directory)
        return {REMOVE_FILES: [yaml_file]}, message

    def deploy(self):
        self.ensure_one()
        self.with_delay().immediate_deploy()

    def immediate_deploy(self):
        self.ensure_one()
        if self.is_master:
            self._apply_repository_changes(self._create_master_application_set)
        else:
            self._apply_repository_changes(self._create_application_set)
        self.is_deployed = True

    def destroy(self):
        self.ensure_one()
        delay = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "argocd.application_set_destruction_delay", "3600"
            )
        )
        self.with_delay(eta=delay).immediate_destroy()

    def immediate_destroy(self):
        self.ensure_one()
        if self.is_master:
            self._apply_repository_changes(self._remove_master_application_set)
        else:
            self._apply_repository_changes(self._remove_application_set)
        self.is_deployed = False

    def abort_destroy(self):
        self.ensure_one()
        jobs = self._find_destroy_queue_jobs()
        for job in jobs:
            job.button_cancelled()
