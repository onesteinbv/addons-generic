import difflib
import os
import re
from pathlib import Path

import jinja2
from git import Repo

from odoo import Command, _, api, fields, models
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
    config_live = fields.Text(compute="_compute_config_live")
    config = fields.Text()
    config_diff = fields.Text(compute="_compute_config_live")
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
    domain_ids = fields.One2many(
        comodel_name="argocd.application.domain",
        inverse_name="application_id",
        string="Domains",
    )
    application_set_id = fields.Many2one("argocd.application.set", required=True)
    is_deployed = fields.Boolean(
        compute="_compute_is_deployed", search="_search_is_deployed"
    )
    is_application_set_deployed = fields.Boolean(
        string="Is App. Set deployed", related="application_set_id.is_deployed"
    )
    stat_ids = fields.One2many(
        comodel_name="argocd.application.stat",
        inverse_name="application_id",
        string="Statistics",
    )

    def get_value(self, key, default=""):
        self.ensure_one()
        kv_pair = self.value_ids.filtered(lambda v: v.key == key)
        if kv_pair:
            return kv_pair.value
        self.value_ids = [Command.create({"key": key, "value": default})]
        return default

    def has_tag(self, key):
        self.ensure_one()
        return bool(self.tag_ids.filtered(lambda t: t.key == key))

    def create_domain(
        self, preferred, *alternatives, scope="global", scope_unique=False, url=True
    ):
        """Shortcut"""
        self.ensure_one()
        return self.env["argocd.application.domain"].create_domain(
            self,
            preferred,
            *alternatives,
            scope=scope,
            scope_unique=scope_unique,
            url=url
        )

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

    @api.depends("application_set_id", "application_set_id.is_deployed", "name")
    def _compute_config_live(self):
        for app in self:
            config_live = ""
            if app.application_set_id and app.name:
                path = Path(
                    app.application_set_id._get_application_deployment_directory(
                        app.name, "ignore"
                    )
                ) / Path("config.yaml")

                if path.is_file():
                    config_live = path.read_text()
            # Compute diff
            diff = difflib.ndiff(
                config_live.splitlines(), (app.config or "").splitlines()
            )
            app.config_diff = "\n".join(diff)
            app.config_live = config_live

    def _search_is_deployed(self, operator, value):
        if operator not in ["=", "!="]:
            raise NotImplementedError("Operator not supported. Use '=' or '!='.")
        if not isinstance(value, bool):
            raise NotImplementedError("Value must be boolean")

        # TODO: When there are many apps, this will be pretty slow. If so,
        #       may need to come up with a better search method.
        if operator == "=" and value or operator == "!=" and not value:
            apps = (
                self.env["argocd.application"]
                .search([])
                .filtered(lambda a: a.is_deployed)
            )
        else:
            apps = (
                self.env["argocd.application"]
                .search([])
                .filtered(lambda a: not a.is_deployed)
            )
        return [("id", "in", apps.ids)]

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
        for scope in self.domain_ids.filtered(lambda l: l.url).mapped("scope"):
            prioritized_domain = self.domain_ids.filtered(
                lambda d: d.scope == scope
            ).sorted("sequence")[0]
            urls.append(
                ("https://%s" % prioritized_domain.name, prioritized_domain.scope)
            )
        return urls

    _sql_constraints = [
        (
            "application_name_unique",
            "unique(name)",
            "Application already exists with this name",
        )
    ]

    @api.constrains("name")
    def _constrain_name(self):
        # We actually need to also do this check if `namespace_prefix_id.name` changes, but it never does in practice
        # FIXME: The namespace_prefix is not necessarily part of the app name depends on the application.set.template
        prefix = self.application_set_id.namespace_prefix_id.name
        if not re.match(
            "^[a-z0-9-]{1,53}$", prefix + self.name
        ):  # lowercase a to z, 0 to 9 and - (dash) are allowed
            raise ValidationError(
                _(
                    "Only lowercase letters, numbers and dashes are allowed in the name (max 53 characters)."
                )
            )

    def _get_config_render_values(self):
        self.ensure_one()
        return {
            "application": self,
            "has_tag": self.has_tag,
            "get_value": self.get_value,
            "create_domain": self.create_domain,
        }

    def render_config(self, context=None):
        for app in self:
            environment = jinja2.Environment()
            template = environment.from_string(app.template_id.config)
            values = app._get_config_render_values()
            values.update(context=context or {})
            app.config = template.render(values)

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
        for app in self:
            if not (app.config or "").strip():
                raise ValidationError(
                    _("Cannot deploy application '%s' with empty configuration.")
                    % app.name
                )
            app.with_delay().immediate_deploy()

    def immediate_destroy(self):
        self.ensure_one()
        self._apply_repository_changes(self._get_destroy_content)

    def destroy(self, eta=0):
        self.ensure_one()
        delay = safe_eval(
            self.env["ir.config_parameter"].get_param(
                "argocd.application_destruction_delay", "0"
            )
        )
        self.message_post(
            subtype_xmlid="argocd_deployer.subtype_application_deletion",
            body=_("Destroying application '%(name)s' in %(eta)s seconds.")
            % {"name": self.name, "eta": eta or delay},
        )
        self.with_delay(eta=eta or delay).immediate_destroy()

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        res = super()._message_auto_subscribe_followers(
            updated_values, default_subtype_ids
        )
        if updated_values.get("application_set_id"):
            res += [
                (p.id, default_subtype_ids, False)
                for p in self.application_set_id.partner_ids
            ]
        return res
