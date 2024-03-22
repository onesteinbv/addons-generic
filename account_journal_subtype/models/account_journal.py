# Copyright 2023 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    subtype = fields.Selection(
        selection=[
            ("general_misc", "Miscellaneous"),
            ("general_depr", "Deprecation"),
            ("general_accr", "Accrual"),
            ("general_tax", "Taxes"),
            ("general_wag", "Wages"),
            ("general_stj", "Inventory revaluation"),
            ("general_fcr", "Foreign currency revaluation"),
            ("general_exch", "Exchange difference"),
        ]
    )
