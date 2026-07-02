import publicWidget from "@web/legacy/js/public/public_widget";
import {Altcha} from "@website_altcha/altcha/altcha.esm";
import {renderToString} from "@web/core/utils/render";

publicWidget.registry.WebsiteMembershipRegistration.include({
    init: function () {
        this._super(...arguments);
        this._altcha = new Altcha();
    },

    willStart: async function () {
        this._altcha.loadLibs();
        return this._super(...arguments);
    },

    start: function () {
        const $form = this.$el.find("form");
        if (this._altcha._publicKey && !$form.find(".o_altcha_widget").length) {
            $form
                .find("button")
                .last() // For a lack of a better selector
                .before(renderToString("website_altcha.AltchaWidget", {}));
        }
        return this._super(...arguments);
    },
});
