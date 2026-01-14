from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    subscription_grace_period = fields.Integer(
        config_parameter="argocd_sale.grace_period", string="Grace Period (in days)"
    )
    subscription_termination_action = fields.Selection(
        selection=[
            ("destroy_app", "Destroy application"),
            ("add_tag", "Add tag"),
        ],
        default="add_tag",
        config_parameter="argocd_sale.termination_action",
    )
    subscription_termination_tag_id = fields.Many2one(
        comodel_name="argocd.application.tag",
        config_parameter="argocd_sale.termination_tag_id",
        string="Tag",
    )
