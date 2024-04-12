# Copyright 2023 Onestein - Anjeel Haria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    donation_frequency = fields.Selection(
        [
            ('onetime', 'One Time'),
            ('monthly', 'Monthly')
        ],
        string='Donation Frequency'
    )
    recurring_donation_provider_reference = fields.Char('Provider Reference For Recurring Donation')
    is_recurring_donation_terminated = fields.Boolean('Is Recurring Donation Terminated')

    def _send_donation_email(self, is_internal_notification=False, comment=None, recipient_email=None):
        self = self.with_context(lang=self.partner_lang)
        return super()._send_donation_email(is_internal_notification, comment, recipient_email)

    def action_terminate_recurring_donation(self):
        # This method needs to be extended in each provider module.
        # This method cancels/terminates the recurring donation on the provider end
        return True


