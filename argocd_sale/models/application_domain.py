from odoo import api, fields, models


class ApplicationDomain(models.Model):
    _inherit = "argocd.application.domain"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        help="Partner associated with this domain.",
        compute="_compute_partner",
        store=True,
    )

    @api.depends("application_id.partner_id")
    def _compute_partner(self):
        for record in self:
            record.partner_id = record.application_id.partner_id
