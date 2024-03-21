import os
import re

import jinja2
import yaml
from git import Repo
from yaml import Loader

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Application(models.Model):
    _name = "argocd.application"
    _description = "ArgoCD Application"
    _inherit = ["mail.thread"]
    _order = "id desc"

    name = fields.Char(required=True)
    template_id = fields.Many2one(
        comodel_name="argocd.application.template", required=True
    )
    config = fields.Text()
    modules = fields.Char(
        string="Modules (as string)",
        help="Comma separated list of modules",
        compute="_compute_modules",
    )
    tag_ids = fields.Many2many(
        comodel_name="argocd.application.tag",
        string="Tags",
    )
    description = fields.Html(
        compute="_compute_description",
        store=True,
    )
    value_ids = fields.One2many(
        comodel_name="argocd.application.value",
        inverse_name="application_id",
        string="Values",
    )
    application_set_id = fields.Many2one(
        "argocd.application.set",
        required=True,
        default=lambda self: self.env.ref("argocd_deployer.application_set_default"),
    )

    def get_value(self, key, default=""):
        self.ensure_one()
        kv_pair = self.value_ids.filtered(lambda v: v.key == key)
        return kv_pair and kv_pair.value or default


    def has_tag(self, key):
        self.ensure_one()
        return bool(self.tag_ids.filtered(lambda t: t.key == key))

    def format_domain(self, subdomain=None):
        """
        Helper method for generating the yaml / helm values. If no domain is specified in e.g. value_ids this can be used
        to make a default domain.
        Uses config parameters `argocd.application_subdomain_format` and `argocd.application_domain_format` for the format.

        @param subdomain: tag key (e.g. matomo)
        @return: formatted domain
        """
        self.ensure_one()
        config_parameter_sudo = self.env["ir.config_parameter"].sudo()
        values = {"application_name": self.name}
        if subdomain:
            domain_format = config_parameter_sudo.get_param(
                "argocd.application_subdomain_format"
            )
            values["subdomain"] = subdomain
        else:
            domain_format = config_parameter_sudo.get_param(
                "argocd.application_domain_format"
            )
        return domain_format % values

    @api.depends("config")
    def _compute_description(self):
        for app in self:
            app.description = app._render_description()

    def _render_description(self):
        self.ensure_one()
        return self.env["ir.qweb"]._render(
            "argocd_deployer.application_description",
            {
                "app": self,
            },
            raise_if_not_found=False,
        )

    def get_urls(self):
        self.ensure_one()
        urls = []
        if not self.config:
            return urls

        config = yaml.load(self.config, Loader=Loader)
        helm = yaml.load(config["helm"], Loader=Loader)
        urls.append(("https://%s" % helm["domain"], "Odoo"))
        for tag in self.tag_ids.filtered(lambda t: t.domain_yaml_path):
            yaml_path = tag.domain_yaml_path.split(".")
            domain = helm
            for p in yaml_path:
                domain = domain.get(p)
                if not domain:
                    raise UserError(
                        _(
                            "Could not find domain in YAML (path: %s)",
                            tag.domain_yaml_path,
                        )
                    )
            urls.append(("https://%s" % domain, tag.name))
        return urls

    @api.depends("tag_ids", "tag_ids.is_odoo_module")
    def _compute_modules(self):
        for application in self:
            application.modules = ",".join(
                application.tag_ids.filtered(lambda t: t.is_odoo_module).mapped("key")
            )

    _sql_constraints = [("application_name_unique", "unique(name)", "Already exists")]

    @api.model
    def find_next_available_name(self, name):
        """
        Find a name which is available based on name (e.g. greg2)

        @param name: a name
        @return: first available name
        """
        if not self.search([("name", "=", name)], count=True):
            return name
        i = 0
        while self.search([("name", "=", name + str(i))], count=True):
            i += 1
        return name + str(i)

    @api.constrains("name")
    def _constrain_name(self):
        if not re.match(
            "^[a-z0-9-]{1,100}$", self.name
        ):  # lowercase a to z, 0 to 9 and - (dash) are allowed
            raise ValidationError(
                _(
                    "Only lowercase letters, numbers and dashes are allowed in the name (max 100 characters)."
                )
            )

    def _get_config_render_values(self):
        self.ensure_one()
        return {
            "application": self,
            "has_tag": self.has_tag,
            "get_value": self.get_value,
            "format_domain": self.format_domain,
        }

    def render_config(self, context=None):
        self.ensure_one()
        environment = jinja2.Environment()
        template = environment.from_string(self.template_id.config)
        values = self._get_config_render_values()
        values.update(context=context or {})
        self.config = template.render(values)

    def deploy(self):
        self.ensure_one()
        self.with_delay().immediate_deploy()

    def _get_repository(self):
        """Get the repository specified in the application set."""
        directory = self.application_set_id._get_repository_directory(allow_create=True)
        if os.path.exists(os.path.join(directory, ".git")):
            return Repo.init(directory)
        else:
            return Repo.clone_from(self.application_set_id.repository_url, directory)

    def _get_remote(self, repository):
        """Find the provided repository's remote repository."""
        return repository.remotes.origin

    def _pull_from_repository(self, repository, remote):
        """Switch to the correct branch, then execute a git pull on the
        repository."""
        repository.git.checkout(self.application_set_id.branch)
        repository.git.reset(
            "--hard", "origin/%s" % self.application_set_id.branch
        )  # Make sure we don't lock after failed push
        remote.pull()

    def _get_application_dir(self, instances_dir, allow_create=True):
        """Returns the directory where the application config is stored locally..
        :param allow_create: bool. If False, the method raises an exception if the
           folder does not exist locally. If True, the folder will be created if it
           does not yet exist."""
        application_dir = os.path.join(instances_dir, self.name)
        if not os.path.exists(application_dir):
            if not allow_create:
                raise UserError(
                    "Application directory (%s) doesn't exist." % application_dir
                )
            os.makedirs(instances_dir, mode=0o775)

    def immediate_deploy(self):
        # TODO: Fix concurrency issue
        # TODO: add automatic healing if conflicts appear whatsoever
        self.ensure_one()

        # Pull repository
        repository = self._get_repository()
        remote = self._get_remote(repository)
        self._pull_from_repository(repository, remote)

        # Make instances directory
        instances_dir = self.application_set_id._get_instances_directory()

        # Create the content of the commit
        message = "Updated application `%s`."
        application_dir = self._get_application_dir(instances_dir)
        config_file = os.path.join(application_dir, "config.yaml")
        if not os.path.exists(config_file):
            message = "Added application `%s`."
        with open(config_file, "w") as fh:
            fh.write(self.config)

        # Add the content, commit and push
        repository.index.add([config_file])
        repository.index.commit(message % self.name)
        remote.push()

    def destroy(self):
        self.ensure_one()
        self.with_delay().immediate_destroy()

    def immediate_destroy(self):
        # TODO: Fix concurrency issue
        # TODO: add automatic healing if conflicts appear whatsoever
        self.ensure_one()

        # Pull repository
        repository = self._get_repository()
        remote = self._get_remote(repository)
        self._pull_from_repository(repository, remote)

        # Remove application directory
        instances_dir = self.application_set_id._get_instances_directory(
            allow_create=False
        )
        application_dir = self._get_application_dir(instances_dir, allow_create=False)
        config_file = os.path.join(application_dir, "config.yaml")
        os.remove(config_file)
        os.removedirs(application_dir)

        # Create the commit and push
        repository.index.remove([config_file])
        repository.index.commit("Removed application `%s`." % self.name)
        remote.push()

        self.unlink()
        action = self.env.ref("argocd_deployer.application_action").read()[0]
        action["target"] = "main"
        return action
