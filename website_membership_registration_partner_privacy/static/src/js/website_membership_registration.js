odoo.define('website_membership_registration_partner_privacy.website_membership_registration', function (require) {
'use strict';
require('website_membership_registration.website_membership_registration');
var publicWidget = require('web.public.widget');
var WebsiteMembershipRegistration = publicWidget.registry.WebsiteMembershipRegistration
WebsiteMembershipRegistration.include({
    events: _.extend({}, WebsiteMembershipRegistration.prototype.events, {
        "change select[name=member_website_privacy]": "_onWebsitePrivacyChange",
        "change input[name=member_publish]": "_onWebsitePrivacyChange",
    }),
    /**
    * @override
    */
    start() {
        const res = this._super(...arguments);
        this._onWebsitePrivacyChange();
        return res
    },
    /**
     * @private
     */
    _onWebsitePrivacyChange: function () {
        var $website_privacy = this.$('select[name="member_website_privacy"]');
        var website_privacy = ($website_privacy.val() || "");
        if(website_privacy === "anonymous"){
            this.$('input[name="member_publish"]').prop('checked', false);
        }
    },

});
});
