# Copyright 2024 Onestein (<http://www.onestein.eu>)


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    print_timesheet_employee = fields.Boolean("Print Employee on Timesheet Report")
