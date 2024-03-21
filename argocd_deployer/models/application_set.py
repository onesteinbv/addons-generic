import os

from odoo import fields, models
from odoo.exceptions import UserError


class ApplicationSet(models.Model):
    _name = "argocd.application.set"
    _description = "ArgoCD Application Set"
    _order = "name asc"

    name = fields.Char(required=True, index=True)
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
    instances_directory = fields.Char(
        required=True,
        help="Folder inside the repository in which to store the application YAML files.",
    )
    domain_format = fields.Char(
        required=True,
        help="The domain format used to build the domain for the deployment.",
    )
    subdomain_format = fields.Char(
        required=True,
        help="The domain format used to build the domain for the deployment.",
    )

    _sql_constraints = [
        ("application_set_name_unique", "unique(name)", "Already exists"),
        (
            "app_set_unique",
            "unique(repository_url, branch, instances_directory)",
            "Another app set is already linked to this repository, branch and instances folder.",
        ),
    ]

    def _get_repository_directory(self, allow_create=True):
        """Returns the directory where the repository is stored locally..
        :param allow_create: bool. If False, the method raises an exception if the
           folder does not exist locally. If True, the folder will be created if it
           does not yet exist."""
        self.ensure_one()
        if not os.path.exists(self.repository_directory):
            if not allow_create:
                raise UserError(
                    "Repository directory (%s) doesn't exist."
                    % self.repository_directory
                )
            os.makedirs(self.repository_directory, mode=0o775)

    def _get_instances_directory(self, allow_create=True):
        """Returns the local instances directory of the repository.
        :param allow_create: bool. If False, the method raises an exception if the
           folder does not exist locally. If True, the folder will be created if it
           does not yet exist."""
        self.ensure_one()
        instances_dir = os.path.join(
            self.repository_directory, self.instances_directory
        )
        if not os.path.exists(instances_dir):
            if not allow_create:
                raise UserError(
                    "Instances directory (%s) doesn't exist." % instances_dir
                )
            os.makedirs(instances_dir, mode=0o775)
