from odoo import fields, models


class SubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    application_ids = fields.One2many(
        comodel_name="argocd.application",
        inverse_name="subscription_line_id",
        help="This is essentially a one2one as subscription_line_id is unique in argocd.application",
    )

    def _to_application_name(self):
        self.ensure_one()
        replacements = {" ": "-", ".": "", "&": "-"}
        # It's not possible to have more than one application linked to a
        # subscription line because of the sql constraint.
        # Let's assume that here.
        product = self.product_id
        partner = self.sale_subscription_id.partner_id.commercial_partner_id
        name = "%s-%s" % (partner.display_name, product.name)
        name = name.strip().lower()
        for replace in replacements:
            name = name.replace(replace, replacements[replace])
        return "".join(c for c in name if c.isalnum() or c == "-")
