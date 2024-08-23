from odoo import fields, models


class ApplicationStat(models.Model):
    _name = "argocd.application.stat"
    _description = "Application Statistics"
    _order = "date desc"

    application_id = fields.Many2one(
        comodel_name="argocd.application", required=True, ondelete="cascade"
    )
    type_id = fields.Many2one(
        comodel_name="argocd.application.stat.type", required=True
    )
    date = fields.Datetime(help="The date when the measurement was done", required=True)
    value = fields.Float()
