import {AltchaLegacyClassFunctionality} from "@website_altcha/altcha.esm";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteMembershipRegistration.include({
    ...AltchaLegacyClassFunctionality,
    altcha_before: "button.btn-primary",
});

publicWidget.registry.WebsiteMembershipRegistration.include({
    // Skip edit mode where the widget would end up being saved
    altcha_insert_widget() {
        if (!this.editableMode) {
            this._super(...arguments);
        }
    },
});
