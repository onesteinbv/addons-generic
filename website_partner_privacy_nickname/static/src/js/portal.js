odoo.define('website_partner_privacy_nickname.portal', function (require) {
'use strict';

require('website_partner_privacy.portal');
var publicWidget = require('web.public.widget');
var portalDetails= publicWidget.registry.portalDetails;
portalDetails.include({
    /**
     * @private
     */
    _onWebsitePrivacyChange: function () {
        this._super();
        var $website_privacy = this.$('select[name="website_privacy"]');
        var website_privacy = ($website_privacy.val() || "");
        if(website_privacy === "nickname"){
            this.$('input[name="nickname"]').prop('required', true);
        }
        else{
            this.$('input[name="nickname"]').prop('required', false);
        }
    },
})
});
