from odoo import api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default helpdesk team values.
        """
        if custom_values is None:
            custom_values = {}
        fetchmail_server_id = self.env.context.get("default_fetchmail_server_id")
        if fetchmail_server_id:
            fetchmail_server = self.env["fetchmail.server"].browse(fetchmail_server_id)
            if fetchmail_server.team_id:
                custom_values.update(
                    {
                        "team_id": fetchmail_server.team_id.id,
                        "user_id": fetchmail_server.team_id.alias_user_id.id,
                    }
                )
        return super().message_new(msg, custom_values=custom_values)
