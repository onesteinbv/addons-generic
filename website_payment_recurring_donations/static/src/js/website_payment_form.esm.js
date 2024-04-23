/** @odoo-module **/
/* Copyright 2023 Onestein - Anjeel Haria
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import checkoutForm from 'payment.checkout_form';

checkoutForm.include({
    // eslint-disable-next-line no-unused-vars
    _prepareTransactionRouteParams: function (code, paymentOptionId, flow) {
        const transactionRouteParams = this._super(...arguments);
        return $('.o_donation_payment_form').length ? {
            ...transactionRouteParams,
            'donation_frequency':this.$('input[name="donation_frequency"]:checked').val(),
        } : transactionRouteParams;
    },
});
