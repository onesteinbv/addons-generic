odoo.define('website_partner_privacy.portal', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var portalDetails= publicWidget.registry.portalDetails;
portalDetails.include({
    events: _.extend({}, portalDetails.prototype.events, {
        'change select[name="website_privacy"]': '_onWebsitePrivacyChange',
        'change input[name="is_published"]': '_onWebsitePrivacyChange',
    }),
    /**
     * @private
     */
    _onWebsitePrivacyChange: function () {
        var $website_privacy = this.$('select[name="website_privacy"]');
        var website_privacy = ($website_privacy.val() || "");
        if(website_privacy === "anonymous"){
            this.$('input[name="is_published"]').prop('checked', false);
        }
    },
})
});
