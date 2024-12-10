# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.depends("date")
    def _compute_week_number(self):
        for line in self:
            week_number = line.date.isocalendar()
            line.week_number = "W%s %s" % (str(week_number[1]), (str(week_number[0])))

    project_user_id = fields.Many2one(
        "res.users", related="project_id.user_id", store=True
    )
    week_number = fields.Char(compute="_compute_week_number", store=True)
