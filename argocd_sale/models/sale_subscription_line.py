from odoo import _, api, fields, models
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
        self.ensure_one()
        replacements = {" ": "-", ".": "", "&": "-"}
        # It's not possible to have more than one application linked to a
        # subscription line because of the sql constraint.
        # Let's assume that here.
        product = self.product_id
        partner = self.sale_subscription_id.partner_id.commercial_partner_id
        name = "%s-%s" % (partner.display_name, product.default_code or product.name)
        name = name.strip().lower()
        for replace in replacements:
            name = name.replace(replace, replacements[replace])
        return "".join(c for c in name if c.isalnum() or c == "-")

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
            app.render_config()
            app.deploy()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_and_destroy_app(self):
        for line in self.filtered(lambda l: l.application_ids):
            delta = line.sale_subscription_id.recurring_next_date - fields.Date.today()
            line.application_ids.destroy(eta=int(delta.total_seconds()))

    def _invoice_paid_hook(self):
        self.ensure_one()
        application_sudo = self.env["argocd.application"].sudo()

        if self.application_ids or not self.product_id.application_template_id:
            return

        name = application_sudo.find_next_available_name(self._to_application_name())
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
