import EventRegistrationForm from "@website_event/js/website_event";
import {Altcha} from "@website_altcha/altcha/altcha.esm";
import {renderToString} from "@web/core/utils/render";

EventRegistrationForm.include({
    init: function () {
        this._super(...arguments);
        this._altcha = new Altcha();
    },

    willStart: async function () {
        this._altcha.loadLibs();
        return this._super(...arguments);
    },

    // Added to inject the Altcha widget into the registration form
    _addTurnstile: function (form) {
        const res = this._super(...arguments);
        const $form = $(form);
        if (
            this._altcha._publicKey &&
            $form.length &&
            !$form.find(".o_altcha_widget").length
        ) {
            const $footer = $form.find(".modal-footer");
            // Insert cleanly right before the Cancel/Confirm buttons
            if ($footer.length) {
                $footer.before(renderToString("website_altcha.AltchaWidget", {}));
            } else {
                $form.append(renderToString("website_altcha.AltchaWidget", {}));
            }
        }
        return res;
    },
});
