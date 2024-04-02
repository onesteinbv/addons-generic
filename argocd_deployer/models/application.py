import os
import re

import jinja2
import yaml
from git import Repo
from yaml import Loader

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

from .repository_base import ADD_FILES, REMOVE_FILES


class Application(models.Model):
    _name = "argocd.application"
    _description = "ArgoCD Application"
    _inherit = ["mail.thread", "argocd.repository.base"]
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
    is_deployed = fields.Boolean(compute="_compute_is_deployed")
    is_application_set_deployed = fields.Boolean(
        string="Is App. Set deployed", related="application_set_id.is_deployed"
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
        values = {"application_name": self.name}
        if subdomain:
            domain_format = self.application_set_id.subdomain_format
            values["subdomain"] = subdomain
        else:
            domain_format = self.application_set_id.domain_format
        return domain_format % values

    @api.depends("config")
    def _compute_description(self):
        for app in self:
            app.description = app._render_description()

    @api.depends("application_set_id", "application_set_id.is_deployed")
    def _compute_is_deployed(self):
        for app in self:
            if not app.is_application_set_deployed:
                app.is_deployed = False
                continue

            path = app.application_set_id._get_application_deployment_directory(
                app.name, "ignore"
            )
            path = os.path.join(
                path,
                "config.yaml",
            )
            app.is_deployed = os.path.isfile(path)

    def _render_description(self):
        self.ensure_one()
        return self.env["ir.qweb"]._render(
            "argocd_deployer.application_description",
            {
                "app": self,
            },
            raise_if_not_found=False,
        )

    @staticmethod
    def _get_domain(helm):
        return helm.get("domain") or helm.get("globals", {}).get("domain")

    def get_urls(self):
        self.ensure_one()
        urls = []
        if not self.config:
            return urls

        config = yaml.load(self.config, Loader=Loader)
        helm = yaml.load(config["helm"], Loader=Loader)
        urls.append(("https://%s" % self._get_domain(helm), "Odoo"))
        for tag in self.tag_ids.filtered(lambda t: bool(t.domain_yaml_path)):
            yaml_path = tag.get_domain_yaml_path(self.application_set_id).split(".")
            domain = helm
            for p in yaml_path:
                domain = domain.get(p)
                if not domain:
                    break
            else:
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

    def _get_repository(self):
        """Get the repository specified in the application set."""
        directory = self.application_set_id._get_application_set_repository_directory(
            "create"
        )
        if os.path.exists(os.path.join(directory, ".git")):
            return Repo.init(directory)
        else:
            return Repo.clone_from(self.application_set_id.repository_url, directory)

    def _get_branch(self):
        """Get the repository branch from the application set."""
        return self.application_set_id.branch

    def _format_commit_message(self, message):
        return message % self.name

    def _get_deploy_content(self):
        """Create the contents of a deploy commit."""
        self.ensure_one()
        application_dir = self.application_set_id._get_application_deployment_directory(
            self.name, "create"
        )
        message = "Updated application `%s`."
        config_file = os.path.join(application_dir, "config.yaml")
        if not os.path.exists(config_file):
            message = "Added application `%s`."
        with open(config_file, "w") as fh:
            fh.write(self.config)
        return {ADD_FILES: [config_file]}, message

    def _get_destroy_content(self):
        """Create the contents of a destroy commit."""
        self.ensure_one()
        message = "Removed application `%s`."
        application_dir = self.application_set_id._get_application_deployment_directory(
            self.name, "error"
        )
        config_file = os.path.join(application_dir, "config.yaml")
        os.remove(config_file)
        os.removedirs(application_dir)
        return {REMOVE_FILES: [config_file]}, message

    def immediate_deploy(self):
        self.ensure_one()
        self._apply_repository_changes(self._get_deploy_content)

    def deploy(self):
        self.ensure_one()
        self.with_delay().immediate_deploy()

    def immediate_destroy(self):
        self.ensure_one()
        self._apply_repository_changes(self._get_destroy_content)

    def destroy(self):
        self.ensure_one()
        delay = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "argocd.application_destruction_delay", "0"
            )
        )
        self.with_delay(eta=delay).immediate_destroy()
