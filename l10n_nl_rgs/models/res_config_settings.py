from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_l10n_nl_rgs = fields.Boolean(
        compute="_compute_is_l10n_nl_rgs",
    )
    l10n_nl_rgs_disable_allowed_journals = fields.Boolean(
        related="company_id.l10n_nl_rgs_disable_allowed_journals",
        readonly=False,
    )

    @api.depends("chart_template")
    def _compute_is_l10n_nl_rgs(self):
        for config in self:
            config.is_l10n_nl_rgs = config.chart_template == "nl_rgs"
