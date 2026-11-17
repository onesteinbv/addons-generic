import hashlib
import json
from datetime import timedelta

from odoo import fields, models


class Subscription(models.Model):
    _inherit = "sale.subscription"

    template_id = fields.Many2one(
        default=lambda self: self._default_subscription_template_id()
    )
    website_id = fields.Many2one(comodel_name="website")

    def _get_default_payment_link_values(self):
        self.ensure_one()
        return {
            "amount": self.amount_total,
            "amount_max": self.amount_total,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
        }

    def _get_payment_checkout_signature(self):
        # Bind the link to the bill-to details and exact line data in this cart.
        self.ensure_one()
        line_values = [
            {
                "id": line.id,
                "product_id": line.product_id.id,
                "name": line.name or "",
                "quantity": line.product_uom_qty,
                "price_unit": line.price_unit,
                "discount": line.discount,
                "tax_ids": sorted(line.tax_ids.ids),
            }
            for line in self.sale_subscription_line_ids.sorted("id")
        ]
        values = {
            "partner_id": self.partner_id.id,
            "end_partner_id": self.end_partner_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "pricelist_id": self.pricelist_id.id,
            "fiscal_position_id": self.fiscal_position_id.id,
            "amount_total": self.amount_total,
            "recurring_next_date": str(self.recurring_next_date or ""),
            "lines": line_values,
        }
        payload = json.dumps(values, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def _default_subscription_template_id(self):
        website = self.env["website"].get_current_website()
        if not website:
            return False
        template_id = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_website.subscription_template_id", "0")
        )
        template = self.env["sale.subscription.template"].browse(template_id)
        return template

    def _cron_cleanup_abandoned(self):
        period = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("argocd_website.subscription_abandoned_period", "0")
        )
        if not period:
            return
        abandoned_date = fields.Datetime.now() - timedelta(days=period)
        self.search(
            [
                ("website_id", "!=", False),
                ("create_date", "<=", fields.Datetime.to_string(abandoned_date)),
                "|",
                ("stage_id.type", "=", "draft"),
                ("stage_id", "=", False),
            ]
        ).unlink()
