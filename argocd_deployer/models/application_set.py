import os
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ApplicationSet(models.Model):
    _name = "argocd.application.set"
    _description = "ArgoCD Application Set"
    _inherit = ["mail.thread"]
    _order = "name asc"
    _rec_name = "description"

    name = fields.Char(required=True, index=True)
    description = fields.Char()
    repository_url = fields.Char(
        required=True, help="URL of the repository that is updated by the applications."
    )
    branch = fields.Char(
        required=True,
        default="master",
        help="The branch on the repository that will be used for deployments in this application set.",
    )
    repository_directory = fields.Char(
        string="Local Directory",
        required=True,
        help="Local path in which the repository is cloned.",
    )
    deployment_directory = fields.Char(
        help="Folder inside the repository in which to store the application YAML files.",
        default="instances",
    )
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Application Followers",
        help="Partners that are automatically added as followers to applications in the application set.",
    )
    namespace_prefix = fields.Char(
        help="Prefix added to the application namespace in ArgoCD", required=True
    )

    _sql_constraints = [
        ("application_set_name_unique", "unique(name)", "Already exists"),
        (
            "app_set_unique",
            "unique(repository_url, branch, deployment_directory)",
            "Another app set is already linked to this repository, branch and instances folder.",
        ),
    ]
    application_ids = fields.One2many(
        "argocd.application", inverse_name="application_set_id"
    )

    @api.constrains("deployment_directory")
    def _check_deployment_directory(self):
        if not self.deployment_directory:
            raise ValidationError(_("Deployment directory is required."))
        if self.deployment_directory[-1] == "/":
            raise ValidationError(_("Deployment directories should not end with '/'."))

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
        """Helper method to create or validate directory paths."""
        if not os.path.exists(path):
            if path_does_not_exist_action == "error":
                raise UserError(f"{directory_name} ({path}) doesn't exist.")
            elif path_does_not_exist_action == "create":
                os.makedirs(path, mode=0o775)
            elif path_does_not_exist_action == "ignore":
                pass
            else:
                raise NotImplementedError("Path does not exist.")

    def _get_application_deployment_directory(
        self, application_name, path_does_not_exist_action="create"
    ):
        """Return the directory where a specific application's YAML files are stored."""
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
