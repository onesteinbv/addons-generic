from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    email = fields.Char(
        "Team Email", help="This would be used when sending out emails to contacts"
    )

    def _notify_get_reply_to(self, default=None):
        """ Override to set reply to email address to that of the helpdesk team if configured likewise"""
        team_email_to_be_used_recs = self.filtered(lambda rec: rec.email and rec.company_id and rec.company_id.helpdesk_mgmt_use_team_email_as_reply_to)
        res = {team.id: team.email for team in team_email_to_be_used_recs}
        leftover = self - team_email_to_be_used_recs
        if leftover:
            res.update(super(HelpdeskTeam, leftover)._notify_get_reply_to(default=default))
        return res