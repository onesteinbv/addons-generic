# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def set_is_approved(cr, registry):
    cr.execute("UPDATE account_analytic_line " "SET is_approved=true")
    return
