import WebsiteMembershipRegistration from "@website_membership_registration/js/website_membership_registration.esm";
WebsiteMembershipRegistration.include({
    events: Object.assign({}, WebsiteMembershipRegistration.prototype.events, {
        "change select[name=member_website_privacy]": "_onWebsitePrivacyChange",
        "change input[name=member_publish]": "_onWebsitePrivacyChange",
    }),
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
