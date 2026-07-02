import portalDetails from "@portal/js/portal";

portalDetails.include({
    /**
     * @private
     */
    _onWebsitePrivacyChange: function () {
        this._super();
        var $website_privacy = this.$('select[name="website_privacy"]');
        var website_privacy = $website_privacy.val() || "";
        if (website_privacy === "nickname") {
            this.$('input[name="nickname"]').prop("required", true);
        } else {
            this.$('input[name="nickname"]').prop("required", false);
        }
    },
});
