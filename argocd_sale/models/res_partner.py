from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_reseller = fields.Boolean()
    reseller_partner_ids = fields.One2many(
        comodel_name="res.partner",
        inverse_name="reseller_id",
        string="Customers",
    )
    reselling_product_ids = fields.Many2many(
        comodel_name="product.template",
        relation="product_reseller_rel",
        string="Reselling Products",
        column1="partner_id",
        column2="product_template_id",
    )
    reseller_id = fields.Many2one(
        comodel_name="res.partner", domain="[('is_reseller', '=', True)]"
    )

    @api.constrains("is_reseller", "reselling_product_ids", "reseller_partner_ids")
    def _check_non_reseller_constraints(self):
        """If the partner is not a reseller, it should not have any reseller products or reseller partners."""
        for partner in self:
            if not partner.is_reseller:
                if partner.reselling_product_ids:
                    raise ValidationError(
                        "A non-reseller partner cannot have reselling products."
                    )
                if partner.reseller_partner_ids:
                    raise ValidationError(
                        "A non-reseller partner cannot have reseller partners."
                    )

    @api.constrains("is_reseller", "reseller_id", "parent_id")
    def _check_reseller_constraints(self):
        """We're also not trying to create a piramide scheme here where a reseller can have another reseller, so we simply
        disallow child partners for resellers.
        """
        for partner in self:
            if partner.is_reseller and partner.reseller_id:
                raise ValidationError(
                    "A partner cannot be a reseller and have a reseller at the same time."
                )
            if partner.is_reseller and partner.parent_id:
                raise ValidationError(
                    "A partner cannot be a reseller and have a parent at the same time."
                )
            if partner.reseller_id and partner.parent_id:
                raise ValidationError(
                    "A partner with a parent cannot have a reseller. Configure the reseller on the parent partner instead."
                )

    @api.constrains("child_ids", "parent_id", "parent_id.is_reseller")
    def _check_reseller_partner_ids(self):
        """
        If the parent is a reseller we won't allow child partners, this enforces a simple hierarchy and avoids misconfiguration.
        By default this cannot be configured using the parent field but a child partner still has the child_ids fields visible.
        """
        for partner in self:
            if (
                partner.parent_id
                and partner.parent_id.is_reseller
                and partner.child_ids
            ):
                raise ValidationError(
                    "A partner with a reseller parent cannot have child partners."
                )

    def to_valid_subdomain(self):
        self.ensure_one()
        replacements = {" ": "-", ".": "", "&": "-", "_": "-"}
        name = self.display_name
        name = name.strip().lower()
        for replace in replacements:
            name = name.replace(replace, replacements[replace])
        return "".join(c for c in name if c.isalnum() or c == "-")
