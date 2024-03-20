from datetime import timedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class Subscription(models.Model):
    _inherit = "sale.subscription"

    application_ids = fields.One2many(
        comodel_name="argocd.application", inverse_name="application_id"
    )

    def _get_grace_period(self):
        return int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_sale.grace_period", "0")
        )

    @api.constrains("sale_subscription_line_ids")
    def _check_multiple_application_products(self):
        app_lines = self.sale_subscription_line_ids.filtered(
            lambda l: l.product_id.application_template_id
        )
        if len(app_lines) > 1:
            raise ValidationError(
                _("Subscription can only have one application, please remove one")
            )

    def _customer_name_to_application_name(self):
        self.ensure_one()
        replacements = {" ": "-", ".": "", "&": "-"}
        partner = self.partner_id.commercial_partner_id
        name = partner.display_name
        name = name.strip().lower()
        for replace in replacements:
            name = name.replace(replace, replacements[replace])
        return "".join(c for c in name if c.isalnum() or c == "-")

    def _invoice_paid_hook(self):
        application_sudo = self.env["argocd.application"].sudo()
        for subscription in self.filtered(
            lambda i: len(i.invoice_ids) == 1
        ):  # Create the application after the first invoice has been paid
            subscription.action_start_subscription()
            lines = subscription.sale_subscription_line_ids.filtered(
                lambda l: l.product_id.application_template_id
            )
            for line in lines:
                name = application_sudo.find_next_available_name(
                    self._customer_name_to_application_name()
                )
                tags = subscription.sale_subscription_line_ids.filtered(
                    lambda l: l.product_id.application_tag_ids
                    and not l.product_id.application_filter_ids  # All lines with modules linked to them
                    or line.product_id.application_template_id  # If there's no filter
                    in l.product_id.application_filter_ids  # If there's a filter
                ).mapped("product_id.application_tag_ids")

                application = application_sudo.create(
                    {
                        "name": name,
                        "subscription_id": subscription.id,
                        "tag_ids": tags.ids,
                        "template_id": line.product_id.application_template_id.id,
                    }
                )
                application.render_config()
                application.deploy()

    def _do_grace_period_action(self):
        grace_period_action = self.env["ir.config_parameter"].get_param(
            "argocd_sale.grace_period_action"
        )
        if not grace_period_action:
            return  # Do nothing
        if grace_period_action == "add_tag":
            grace_period_tag_id = self.env["ir.config_parameter"].get_param(
                "argocd_sale.grace_period_tag_id", "0"
            )
            if not grace_period_tag_id:
                return
            tag = self.env["argocd.application.tag"].browse(grace_period_tag_id)
            if not tag:
                return
            self.mapped("application_ids").write({"tag_ids": [Command.link(tag)]})
        elif grace_period_action == "delete_app":
            self.mapped("application_ids").destroy()

    def cron_update_payment_provider_subscriptions(self):
        # Process last payments first in here last_date_invoiced can be updated
        res = super().cron_update_payment_provider_subscriptions()
        period = self._get_grace_period()
        if not period:
            return res
        today = fields.Date.today()
        late_date = today - timedelta(days=period)
        late_subs = self.search(
            [("last_date_invoiced", "<", late_date), ("in_progress", "=", True)]
        )
        if late_subs:
            late_subs.close_subscription()
            late_subs._do_grace_period_action()
        return res
