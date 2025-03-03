# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, tools


class Company(models.Model):
    _inherit = "res.company"

    def _default_alias_domain_id(self):
        return self.env['mail.alias.domain'].search([], limit=1)

    alias_domain_id = fields.Many2one(
        'mail.alias.domain', string='Email Domain',
        default=lambda self: self._default_alias_domain_id())
    alias_domain_name = fields.Char('Alias Domain Name', related='alias_domain_id.name', readonly=True, store=True)
    default_from_email = fields.Char(
        string="Default From", related="alias_domain_id.default_from_email",
        readonly=True)
    bounce_email = fields.Char(string="Bounce Email", compute="_compute_bounce")
    bounce_formatted = fields.Char(string="Bounce", compute="_compute_bounce")
    catchall_email = fields.Char(string="Catchall Email", compute="_compute_catchall")
    catchall_formatted = fields.Char(string="Catchall", compute="_compute_catchall")

    @api.depends('alias_domain_id', 'name')
    def _compute_bounce(self):
        self.bounce_email = ''
        self.bounce_formatted = ''

        for company in self.filtered('alias_domain_id'):
            bounce_email = company.alias_domain_id.bounce_email
            company.bounce_email = bounce_email
            company.bounce_formatted = tools.formataddr((company.name, bounce_email))

    @api.depends('alias_domain_id', 'name')
    def _compute_catchall(self):
        self.catchall_email = ''
        self.catchall_formatted = ''

        for company in self.filtered('alias_domain_id'):
            catchall_email = company.alias_domain_id.catchall_email
            company.catchall_email = catchall_email
            company.catchall_formatted = tools.formataddr((company.name, catchall_email))
