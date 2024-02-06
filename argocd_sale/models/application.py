from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Application(models.Model):
    _inherit = "argocd.application"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_partner_id",
        store=True,
        readonly=False,
    )

    def is_created_by_reseller(self):
        self.ensure_one()
        return self.partner_id.is_reseller or (
            self.partner_id.parent_id and self.partner_id.parent_id.is_reseller
        )

    invoice_id = fields.Many2one(comodel_name="account.move")

    @api.depends("invoice_id", "invoice_id.partner_id")
    def _compute_partner_id(self):
        for app in self.filtered(lambda a: a.invoice_id):
            app.partner_id = app.invoice_id.partner_id

    def _get_deployment_notification_mail_template(self):
        self.ensure_one()
        return "argocd_sale.deployment_notification_mail_template"

    def send_deployment_notification(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Please provide a partner"))
        mail_template_id = self._get_deployment_notification_mail_template()
        template = self.env.ref(mail_template_id)
        template.sudo().send_mail(self.id, force_send=True)

    def deploy(self):
        res = super().deploy()
        if self.template_id.auto_send_deployment_notification and self.partner_id:
            self.send_deployment_notification()
        return res
