from odoo import models


class AccountMove(models.Model):
    _inherit = "acccount.move"

    def action_post(self):
        return super().action_post()
