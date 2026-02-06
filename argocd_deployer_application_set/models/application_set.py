import difflib
import os
from pathlib import Path

from git import Repo

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.argocd_deployer.models.repository_base import ADD_FILES, REMOVE_FILES


class ApplicationSet(models.Model):
    _inherit = ["argocd.application.set", "argocd.repository.base"]

    template_id = fields.Many2one("argocd.application.set.template", required=True)

    # Master application set relationship
    is_master = fields.Boolean(
        default=False,
        compute="_compute_is_master",
        store=True,
        help="Indicates that this is the master application set. "
        "This set must be manually installed in ArgoCD.",
    )
    master_application_set_id = fields.Many2one(comodel_name="argocd.application.set")
    is_deployed = fields.Boolean(compute="_compute_is_deployed")
    has_deployed_applications = fields.Boolean(
        compute="_compute_has_deployed_applications"
    )
    is_destroying = fields.Boolean(compute="_compute_is_destroying")
    config_live = fields.Text(compute="_compute_config_live")
    config = fields.Text()
    config_diff = fields.Text(compute="_compute_config_live")

    @api.depends("master_application_set_id")
    def _compute_is_master(self):
        for app_set in self:
            app_set.is_master = not bool(app_set.master_application_set_id)

    def _get_master_repository_directory(self, path_does_not_exist_action="create"):
        """Return the directory where the master repository is cloned."""
        self.ensure_one()
        master = self.master_application_set_id or self
        path = os.path.join(
            master.local_repository_directory,
            master._get_git_branch(),
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
            master._get_git_deployment_directory(),
        )
        self._create_path_or_error(
            path, "Master deployment directory", path_does_not_exist_action
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
            "{{.application_set.namespace_prefix}}": self.namespace_prefix
            or "",
        }
        template_yaml = self.template_id.yaml
        for key, value in replacements.items():
            template_yaml = template_yaml.replace(key, value)
        return template_yaml

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
            return Repo.clone_from(self._get_git_repository_url(), directory)

    def _get_repository(self):
        """Get the repository specified in the application set."""
        directory = self._get_master_repository_directory("create")
        if os.path.exists(os.path.join(directory, ".git")):
            return Repo.init(directory)
        else:
            return Repo.clone_from(self._get_git_repository_url(), directory)

    def _get_branch(self):
        return self._get_git_branch()

    def _format_commit_message(self, message):
        return message % self.name

    def _create_master_application_set(self):
        """The master application set will be deployed in a master_application_set folder
        in the root of the repository. There will be a templates folder in it, and a
        Chart.yaml file."""
        self.ensure_one()
        repo_dir = self._get_master_repository_directory("create")
        application_set_dir = os.path.join(repo_dir, "master_application_set")
        template_dir = os.path.join(application_set_dir, "templates")
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        message = "Added application set `%s`."

        yaml_file = os.path.join(template_dir, "application_set.yaml")
        with open(yaml_file, "w") as fh:
            fh.write(self.config)

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
        deployment_directory = self._get_application_set_deployment_directory("create")
        if not os.path.exists(deployment_directory):
            os.makedirs(deployment_directory)

        yaml_file = os.path.join(deployment_directory, "application_set.yaml")
        message = "Added application set `%s`."
        with open(yaml_file, "w") as fh:
            fh.write(self.config)

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

    def _compute_config_live(self):
        for app_set in self:
            if app_set.is_master:
                path = Path(app_set._get_master_repository_directory("ignore"))
                path = path / Path(
                    "master_application_set/templates/application_set.yaml"
                )
            else:
                path = Path(app_set._get_application_set_deployment_directory("ignore"))
                path = path / Path("application_set.yaml")
            if path.is_file():
                app_set.config_live = path.read_text()
            else:
                app_set.config_live = ""

            diff = difflib.ndiff(
                app_set.config_live.splitlines(), (app_set.config or "").splitlines()
            )
            app_set.config_diff = "\n".join(diff)

    def render_config(self):
        for app_set in self:
            app_set.config = app_set._get_argocd_template()
