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
    domain = fields.Char(compute="_compute_domain", store=True)
    description = fields.Html(
        compute="_compute_description",
        store=True,
    )
    value_ids = fields.One2many(
        comodel_name="argocd.application.value",
        inverse_name="application_id",
        string="Values",
    )

    def get_value(self, key, default=False):
        self.ensure_one()
        kv_pair = self.value_ids.filtered(lambda v: v.key == key)
        return kv_pair and kv_pair.value or default

    def has_tag(self, key):
        self.ensure_one()
        return bool(self.tag_ids.filtered(lambda t: t.key == key))

    @api.depends("config")
    def _compute_domain(self):
        for record in self:
            domain = False
            if record.config:
                config = yaml.load(record.config, Loader=Loader)
                helm = yaml.load(config["helm"], Loader=Loader)
                domain = helm["domain"]
            record.domain = domain

    @api.depends("domain", "tag_ids", "tag_ids.subdomain")
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
        if self.domain:
            urls.append(("https://%s" % self.domain, "Odoo"))
        urls += [
            ("https://%s.%s" % (tag.subdomain, self.domain), tag.name)
            for tag in self.tag_ids.filtered(lambda t: t.subdomain)
        ]
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
        """Returns a name which is available based on name (e.g. greg2)"""
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

    @api.model
    def _get_parameters(self):
        repo_url = self.env["ir.config_parameter"].get_param(
            "argocd.application_set_repo"
        )
        branch = self.env["ir.config_parameter"].get_param(
            "argocd.application_set_branch", "master"
        )
        repo_dir = self.env["ir.config_parameter"].get_param(
            "argocd.application_set_repo_directory"
        )
        instances_dir = self.env["ir.config_parameter"].get_param(
            "argocd.application_set_directory"
        )

        if not repo_url:
            raise UserError(
                _("System parameter `argocd.application_set_repo` is not configured.")
            )
        if not repo_dir:
            raise UserError(
                _(
                    "System parameter `argocd.application_set_repo_directory` is not configured."
                )
            )
        if not instances_dir:
            raise UserError(
                _(
                    "System parameter `argocd.application_set_directory` is not configured."
                )
            )

        return {
            "repo_url": repo_url,
            "branch": branch,
            "repo_dir": repo_dir,
            "instances_dir": instances_dir,
        }

    def _get_config_render_values(self):
        self.ensure_one()
        return {
            "application": self,
            "has_tag": self.has_tag,
            "get_value": self.get_value,
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

    def immediate_deploy(self):
        # TODO: Fix concurrency issue
        # TODO: add automatic healing if conflicts appear whatsoever
        self.ensure_one()
        params = self._get_parameters()
        repo_dir = params["repo_dir"]
        instances_dir = params["instances_dir"]
        repo_url = params["repo_url"]
        branch = params["branch"]

        # Pull repo
        if os.path.exists(os.path.join(repo_dir, ".git")):
            repo = Repo.init(repo_dir)
        else:
            repo = Repo.clone_from(repo_url, repo_dir)
        repo.git.checkout(branch)
        repo.git.reset(
            "--hard", "origin/%s" % branch
        )  # Make sure we don't lock after failed push
        remote = repo.remotes.origin
        remote.pull()

        # Make instances directory
        instances_dir = os.path.join(repo_dir, instances_dir)
        if not os.path.exists(instances_dir):
            os.makedirs(instances_dir, mode=0o775)

        # Create application directory
        is_new_application = False
        application_dir = os.path.join(instances_dir, self.name)
        if not os.path.exists(application_dir):
            os.makedirs(application_dir, mode=0o775)

        config_file = os.path.join(application_dir, "config.yaml")
        if not os.path.exists(config_file):
            is_new_application = True

        # Write file
        with open(config_file, "w") as fh:
            fh.write(self.config)

        # Commit and push
        repo.index.add([config_file])
        message = (
            is_new_application
            and "Added application `%s`"
            or "Updated application `%s`"
        )
        repo.index.commit(message % self.name)
        remote.push()

    def destroy(self):
        self.ensure_one()
        self.with_delay().immediate_destroy()

    def immediate_destroy(self):
        # TODO: Fix concurrency issue
        # TODO: add automatic healing if conflicts appear whatsoever
        self.ensure_one()
        params = self._get_parameters()
        repo_dir = params["repo_dir"]
        instances_dir = params["instances_dir"]
        repo_url = params["repo_url"]
        branch = params["branch"]

        # Pull repo
        if os.path.exists(os.path.join(repo_dir, ".git")):
            repo = Repo.init(repo_dir)
        else:
            repo = Repo.clone_from(repo_url, repo_dir)
        repo.git.checkout(branch)
        repo.git.reset(
            "--hard", "origin/%s" % branch
        )  # Make sure we don't lock after failed push
        remote = repo.remotes.origin
        remote.pull()

        # Check instances directory exists
        instances_dir = os.path.join(repo_dir, instances_dir)
        if not os.path.exists(instances_dir):
            raise UserError("Instances directory doesn't exists (%s)" % instances_dir)

        # Remove application directory
        application_dir = os.path.join(instances_dir, self.name)
        if not os.path.exists(application_dir):
            raise UserError(
                "Application directory doesn't exists (%s)" % application_dir
            )
        config_file = os.path.join(application_dir, "config.yaml")
        os.remove(config_file)
        os.removedirs(application_dir)

        # Commit and push
        repo.index.remove([config_file])
        repo.index.commit("Removed application `%s`" % self.name)
        remote.push()

        self.unlink()
        action = self.env.ref("argocd_deployer.application_action").read()[0]
        action["target"] = "main"
        return action
