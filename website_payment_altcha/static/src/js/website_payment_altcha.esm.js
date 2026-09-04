import PaymentForm from "@payment/js/payment_form";
import {Altcha} from "@website_altcha/altcha/altcha.esm";
import {renderToString} from "@web/core/utils/render";
import {_t} from "@web/core/l10n/translation";

PaymentForm.include({
    init() {
        this._super(...arguments);
        if (document.querySelector(".o_donation_payment_form")) {
            this._altcha = new Altcha();
        }
    },

    willStart() {
        if (document.querySelector(".o_donation_payment_form")) {
            this._altcha.loadLibs();
        }
        return this._super(...arguments);
    },

    start() {
        const res = this._super(...arguments);
        if (
            document.querySelector(".o_donation_payment_form") &&
            !this.$el.find(".o_altcha_widget").length &&
            this._altcha._publicKey
        ) {
            this.$el
                .find("[name='o_payment_submit_button']")
                .parent()
                .before(renderToString("website_altcha.AltchaWidget", {}));
        }
        return res;
    },

    async _initiatePaymentFlow() {
        if (
            document.querySelector(".o_donation_payment_form") &&
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
        if (
            document.querySelector(".o_donation_payment_form") &&
            this._altcha._publicKey
        ) {
            return {
                ...transactionRouteParams,
                altcha: this.$el.find("input[name='altcha']").val(),
            };
        }
        return transactionRouteParams;
    },
});
