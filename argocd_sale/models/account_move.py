from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains("invoice_line_ids")
    def _check_multiple_application_products(self):
        app_lines = self.line_ids.filtered(
            lambda l: l.product_id.application_template_id
        )
        if len(app_lines) > 1:
            raise ValidationError(
                _("Invoice can only have one application, please remove one")
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
        for invoice in self.filtered(lambda i: not i.subscription_id):
            lines = invoice.line_ids.filtered(
                lambda l: l.product_id.application_template_id
            )
            for line in lines:
                name = application_sudo.find_next_available_name(
                    self._customer_name_to_application_name()
                )
                tags = invoice.line_ids.filtered(
                    lambda l: l.product_id.application_tag_ids
                    and not l.product_id.application_filter_ids  # All lines with modules linked to them
                    or line.product_id.application_template_id  # If there's no filter
                    in l.product_id.application_filter_ids  # If there's a filter
                ).mapped("product_id.application_tag_ids")

                application = application_sudo.create(
                    {
                        "name": name,
                        "invoice_id": invoice.id,
                        "tag_ids": tags.ids,
                        "template_id": line.product_id.application_template_id.id,
                    }
                )
                application.render_config()
                application.deploy()

        return super(AccountMove, self)._invoice_paid_hook()
