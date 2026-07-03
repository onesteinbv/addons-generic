/* Copyright 2023 Onestein - Anjeel Haria
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import publicWidget from "@web/legacy/js/public/public_widget";
const DonationSnippet = publicWidget.registry.DonationSnippet;
DonationSnippet.include({
    events: Object.assign({}, DonationSnippet.prototype.events, {
        "click .donation_frequency": "_onClickDonationFrequency",
    }),

    _onClickDonationFrequency(ev) {
        const $button = $(ev.currentTarget);
        this.$(".donation_frequency").parent("label").removeClass("active");
        $button.parent("label").addClass("active");
    },
});
