from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError


class SubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    application_ids = fields.One2many(
        comodel_name="argocd.application",
        inverse_name="subscription_line_id",
        help="This is essentially a one2one as subscription_line_id"
        " is unique in argocd.application",
    )

    def _to_application_name(self):
        """
        @return: a unique yet human-readable name to use as application name
        """
        self.ensure_one()
        replacements = {" ": "-", ".": "", "&": "-"}
        # It's not possible to have more than one application linked to a
        # subscription line because of the sql constraint.
        # Let's assume that here.
        product = self.product_id
        partner = self.sale_subscription_id.partner_id.commercial_partner_id
        # Add id to the end to easily ensure uniqueness
        name = "-".join(
            [partner.display_name, product.default_code or product.name, str(self.id)]
        )
        name = name.strip().lower()
        for replace in replacements:
            name = name.replace(replace, replacements[replace])
        app_name = "".join(c for c in name if c.isalnum() or c == "-")
        while "--" in app_name:  # Never 2 dashes after each other
            app_name = app_name.replace("--", "-")
        # FIXME: The namespace_prefix is not necessarily part of the app name depends on the application.set.template
        prefix = self.product_id.application_set_id.namespace_prefix_id.name
        full_app_name = prefix + app_name
        while len(full_app_name) > 53 or app_name[0] == "-":
            app_name = app_name[1:]
            full_app_name = prefix + app_name
        return app_name

    def write(self, vals):
        to_redeploy = self.env["argocd.application"]
        if "product_id" in vals:
            product = self.env["product.product"].browse(vals["product_id"])
            # TODO: Enforce only up here e.g. 50GB to 20GB in some cases should not be allowed, but 5 users to 4 should
            changed_lines = self.filtered(
                lambda l: l.application_ids and product != l.product_id
            )
            invalid_changes = changed_lines.filtered(
                lambda l: product.product_tmpl_id != l.product_id.product_tmpl_id
            )
            # TODO: Enforce only up here e.g. 50GB to 20GB in some cases should not be allowed, but 5 users to 4 should
            if invalid_changes:
                raise UserError(
                    _(
                        "This variant has a different product template, please create a new line and delete this one instead."
                    )
                )
            to_redeploy += changed_lines.mapped("application_ids")

        if "product_uom_qty" in vals:
            qty = int(
                vals["product_uom_qty"]
            )  # Cast to int just to make sure. I'm not sure if it's required
            to_redeploy += self.filtered(
                lambda l: l.application_ids and l.product_uom_qty != qty
            ).mapped("application_ids")
        res = super().write(vals)
        for app in to_redeploy:
            app.render_config()  # Rerender config according to new product
        return res
    
    def _terminate_applications(self, eta=None):
        self.with_delay(eta=eta)._immediate_terminate_applications()

    def _immediate_terminate_applications(self):
        """
        Executes the termination action on self.

        @return: False if nothing has been done, True if the action has been done
        """
        termination_action = self.env["ir.config_parameter"].get_param(
            "argocd_sale.termination_action"
        )
        if not termination_action:
            return False

        applications = self.mapped("application_ids")

        if termination_action == "add_tag":
            termination_tag_id = int(
                self.env["ir.config_parameter"].get_param(
                    "argocd_sale.termination_tag_id", "0"
                )
            )
            if not termination_tag_id:
                return False
            tag = self.env["argocd.application.tag"].browse(termination_tag_id)
            if not tag:
                return False
            applications.write({"tag_ids": [Command.link(tag.id)]})
            applications.render_config()
        elif termination_action == "destroy_app":
            applications.destroy()
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_and_terminate_app(self):
        self._terminate_applications()

    def _invoice_paid_hook(self):
        self.ensure_one()
        application_sudo = self.env["argocd.application"].sudo()

        if self.application_ids or not self.product_id.application_template_id:
            return

        name = self._to_application_name()
        application = application_sudo.create(
            {
                "name": name,
                "subscription_line_id": self.id,
                "tag_ids": self.product_id.application_tag_ids.ids,
                "template_id": self.product_id.application_template_id.id,
                "application_set_id": self.product_id.application_set_id.id,
            }
        )
        application.render_config()
        application.deploy()
