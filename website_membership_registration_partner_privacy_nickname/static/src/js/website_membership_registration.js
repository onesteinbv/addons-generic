odoo.define('website_membership_registration_partner_privacy_nickname.website_membership_registration', function (require) {
'use strict';
require('website_membership_registration_partner_privacy.website_membership_registration');
var publicWidget = require('web.public.widget');
var WebsiteMembershipRegistration = publicWidget.registry.WebsiteMembershipRegistration
WebsiteMembershipRegistration.include({
    /**
     * @private
     */
    _onWebsitePrivacyChange: function () {
        this._super();
        var $website_privacy = this.$('select[name="member_website_privacy"]');
        var website_privacy = ($website_privacy.val() || "");
        if(website_privacy === "nickname"){
            this.$('input[name="member_nickname"]').prop('required', true);
        }
        else{
            this.$('input[name="member_nickname"]').prop('required', false);
        }
    },

});
});
