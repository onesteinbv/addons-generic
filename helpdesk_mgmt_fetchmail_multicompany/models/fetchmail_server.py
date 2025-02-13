# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Helpdesk Team",
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]",
    )
    has_helpdesk_ticket_object = fields.Boolean(
        compute="_compute_has_helpdesk_ticket_object"
    )

    @api.depends("object_id")
    def _compute_has_helpdesk_ticket_object(self):
        for rec in self:
            rec.has_helpdesk_ticket_object = (
                True
                if (rec.object_id and rec.object_id.model == "helpdesk.ticket")
                else False
            )

    @api.onchange("company_id", "object_id")
    def _onchange_company_id(self):
        self.team_id = False
