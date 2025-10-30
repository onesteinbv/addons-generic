from odoo import _, api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def action_ticket_send(self):
        self.ensure_one()
        template = self.env.ref(
            "helpdesk_mgmt_email.helpdesk_ticket_created_email_template", False
        )
        compose_form = self.env.ref("mail.email_compose_message_wizard_form")
        ctx = dict(
            default_model="helpdesk.ticket",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)
        tickets_to_send_email_for = []
        for ticket in tickets:
            if (
                ticket.company_id
                and ticket.company_id.helpdesk_mgmt_send_email_on_ticket_creation
                and (ticket.partner_id or ticket.partner_email)
            ):
                tickets_to_send_email_for += [ticket.id]
        if tickets_to_send_email_for:
            server_action = self.env.ref(
                "helpdesk_mgmt_email.email_on_ticket_creation", raise_if_not_found=False
            )
            if server_action:
                ctx = {
                    "active_model": self._name,
                    "active_ids": tickets_to_send_email_for,
                }
                server_action.with_context(**ctx).run()
        return tickets
