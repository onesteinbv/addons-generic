from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_website_share_friendica = fields.Boolean("")
    module_website_sale_share_friendica = fields.Boolean("")
    website_share_friendica = fields.Boolean(
        related="website_id.share_friendica", readonly=False
    )
