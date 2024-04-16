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

    subscription_id = fields.Many2one(comodel_name="sale.subscription")

    @api.depends("subscription_id", "subscription_id.partner_id")
    def _compute_partner_id(self):
        for app in self.filtered(lambda a: a.subscription_id):
            app.partner_id = app.subscription_id.partner_id

    def _get_queue_mail_template(self):
        self.ensure_one()
        return False

    def _get_deployment_mail_template(self):
        self.ensure_one()
        if not self.template_id.send_deployment_mail:
            return False
        if self.is_deployed:
            return "argocd_sale.redeployment_mail_template"
        return "argocd_sale.deployment_mail_template"

    def send_queue_mail(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Please provide a partner"))
        mail_template_id = self._get_queue_mail_template()
        if not mail_template_id:
            return
        template = self.env.ref(mail_template_id)
        template.sudo().send_mail(self.id, force_send=True)

    def immediate_deploy(self):
        self.ensure_one()
        mail_template_id = self._get_deployment_mail_template()
        res = super().immediate_deploy()
        if not self.partner_id or not mail_template_id:
            return res
        template = self.env.ref(mail_template_id)
        template.sudo().send_mail(self.id, force_send=True)
        return res

    def deploy(self):
        res = super().deploy()
        if self.partner_id:
            self.send_queue_mail()
        return res
