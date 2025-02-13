from odoo import _, models


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
