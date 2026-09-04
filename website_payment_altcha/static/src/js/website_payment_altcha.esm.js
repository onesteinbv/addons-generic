import {AltchaLegacyClassFunctionality} from "@website_altcha/altcha.esm";
import PaymentForm from "@payment/js/payment_form";
import {_t} from "@web/core/l10n/translation";

PaymentForm.include({
    ...AltchaLegacyClassFunctionality,
    altcha_before: "div:has([name='o_payment_submit_button'])",
});

PaymentForm.include({
    async _initiatePaymentFlow() {
        if (
            document.querySelector(".o_donation_payment_form") &&
            this.altcha_enabled &&
            !this.$el.find("input[name='altcha']").val()
        ) {
            this._displayErrorDialog(
                _t("Payment processing failed"),
                _t("Please complete the Altcha verification.")
            );
            this._enableButton();
            return;
        }
        await this._super(...arguments);
    },

    _prepareTransactionRouteParams() {
        const transactionRouteParams = this._super(...arguments);
        if (document.querySelector(".o_donation_payment_form") && this.altcha_enabled) {
            return {
                ...transactionRouteParams,
                altcha: this.$el.find("input[name='altcha']").val(),
            };
        }
        return transactionRouteParams;
    },
});
