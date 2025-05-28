/* Copyright 2023 Onestein - Anjeel Haria
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({
    _prepareTransactionRouteParams() {
        const transactionRouteParams = this._super(...arguments);
        // eslint-disable-next-line no-undef
        return document.querySelector('.o_donation_payment_form') ? {
            ...transactionRouteParams,
            'donation_frequency':this.$('input[name="donation_frequency"]:checked').val(),
        } : transactionRouteParams;
    },
});
