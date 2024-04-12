# Copyright 2023 Onestein - Anjeel Haria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from werkzeug import urls
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
import logging

from odoo import _, models, fields
from odoo.addons.payment_mollie.controllers.main import MollieController

_logger = logging.getLogger(__name__)
DONATION_FREQUENCY_MAP = {'monthly': 'months'}


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_transaction_customer_id(self):
        mollie_customer_id = False
        if self.is_donation and self.partner_id:
            partner_obj = self.partner_id
            if partner_obj.mollie_customer_id:
                mollie_customer_id = partner_obj.mollie_customer_id
            else:
                customer_id_data = self.provider_id.with_context(partner=partner_obj.id)._api_mollie_create_customer_id()
                if customer_id_data and customer_id_data.get('id'):
                    mollie_customer_id = customer_id_data.get('id')
                    partner_obj.write({'mollie_customer_id': mollie_customer_id})
        return mollie_customer_id

    def _process_notification_data(self, data):
        """
        Overriden method for handling donation transactions
        """
        if self.provider_code != 'mollie' or self.sale_order_ids:
            return super()._process_notification_data(data)

        self._process_refund_transactions_status()

        provider_reference = self.provider_reference
        mollie_payment = self.provider_id._api_mollie_get_payment_data(provider_reference)
        payment_status = mollie_payment.get('status')
        if (
                (payment_status in ['paid', 'done'] and self.state == 'done') or
                (payment_status in ['pending', 'open'] and self.state == 'pending') or
                (payment_status == 'authorized' and self.state == 'authorized')
        ):
            return
        if payment_status in ['paid', 'done', 'pending', 'authorized']:
            if self.is_donation and self.donation_frequency != 'onetime':
                self._mollie_create_donation_subscription(mollie_payment)
        if payment_status in ['paid', 'done']:
            self._set_done()
        elif payment_status in ['pending', 'open']:
            self._set_pending()
        elif payment_status == 'authorized':
            self._set_authorized()
        elif payment_status in ['expired', 'canceled', 'failed']:
            self._set_canceled("Mollie: " + _("Mollie: canceled due to status: %s", payment_status))
        else:
            self._set_error("Mollie: " + _("Received data with invalid payment status: %s", payment_status))

    def _mollie_create_donation_subscription(self, mollie_payment):
        self.ensure_one()
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        amount = {
            'currency': self.currency_id.name,
            'value': "%.2f" % (self.amount + self.fees)
        }
        interval = '{} {}'.format(1, DONATION_FREQUENCY_MAP[self.donation_frequency])
        description = '{} - {}'.format(self.partner_id.name + 'Donation', self.reference)
        webhook_url = ''
        webhook_urls = urls.url_join(mollie.get_base_url(), MollieController._webhook_url)
        if "://localhost" not in webhook_urls and "://192.168." not in webhook_urls:
            webhook_url = webhook_urls
        mollie_customer_id = self._get_transaction_customer_id()
        customer = mollie_client.customers.get(mollie_customer_id)
        data = {
            'amount': amount or '',
            'interval': interval or '',
            'description': description or '',
            'webhookUrl': webhook_url,
            'startDate': self._get_start_date(),
            'mandateId': mollie_payment and mollie_payment['mandateId'] or ''
        }
        subscription = customer.subscriptions.create(data)
        if subscription and subscription['resource'] == 'subscription':
            self.recurring_donation_provider_reference = subscription['id'] or ''

    def _get_start_date(self):
        start_date = date.today()
        if self.donation_frequency:
            if DONATION_FREQUENCY_MAP[self.donation_frequency] == 'months':
                start_date = date.today() + relativedelta(months=1)
        return start_date.strftime("%Y-%m-%d")

    def _create_mollie_order_or_payment(self):
        """
        Overriden this method for handing the donation transactions
        """
        self.ensure_one()
        method_record = self.provider_id.mollie_methods_ids.filtered(
            lambda m: m.method_code == self.mollie_payment_method)

        if (self.is_donation and self.donation_frequency != 'onetime' and method_record.supports_payment_api):
            result = self.with_context(first_mollie_donation_payment=True)._mollie_create_payment_record('payment')
            if result:
                return result
        return super()._create_mollie_order_or_payment()

    def _mollie_prepare_payment_payload(self, api_type):
        payment_data, params = super(PaymentTransaction, self)._mollie_prepare_payment_payload(api_type)

        if self._context.get("first_mollie_donation_payment"):
            payment_data.update({
                'description': 'First Payment for {} - {}'.format(self.partner_id.name + 'Donation', self.reference),
                'sequenceType': 'first'
            })
        mollie_customer_id = self._get_transaction_customer_id()
        if api_type == 'order':
            payment_data['payment']["customerId"] = mollie_customer_id
        else:
            payment_data["customerId"] = mollie_customer_id
        return payment_data, params

    def action_terminate_recurring_donation(self):
        if self.provider_id.code != 'mollie':
            return super().action_terminate_recurring_donation()
        mollie = self.env.ref("payment.payment_provider_mollie")
        mollie_client = mollie._api_mollie_get_client()
        try:
            customer = mollie_client.customers.get(self.partner_id.mollie_customer_id)
            subscription = customer.subscriptions.delete(self.recurring_donation_provider_reference)
            if subscription:
                canceled_date = False
                if 'canceledAt' in subscription.keys():
                    canceled_date = datetime.strptime(subscription.get('canceledAt')[0:19], "%Y-%m-%dT%H:%M:%S")
                msg = _("<b>The recurring donation on mollie has been terminated on %s" % (canceled_date))
                self.sudo().message_post(body=msg)
        except Exception:
            _logger.info(_('Mollie customer or subscription not found'))
        # marking all related payment transactions for recurring donations having same provider reference as terminated.
        self.search(
            [('recurring_donation_provider_reference', '=', self.recurring_donation_provider_reference)]).write(
            {'is_recurring_donation_terminated': True})
        return True
