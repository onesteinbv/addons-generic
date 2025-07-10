import portalDetails from "@portal/js/portal";

portalDetails.include({
    events: Object.assign({}, portalDetails.prototype.events, {
        'change select[name="website_privacy"]': '_onWebsitePrivacyChange',
        'change input[name="is_published"]': '_onWebsitePrivacyChange',
    }),
    /**
     * @private
     */
    _onWebsitePrivacyChange() {
        var $website_privacy = this.$('select[name="website_privacy"]');
        var website_privacy = ($website_privacy.val() || "");
        if(website_privacy === "anonymous"){
            this.$('input[name="is_published"]').prop('checked', false);
        }
    },
});
