import WebsiteMembershipRegistration from "@website_membership_registration/js/website_membership_registration.esm";
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
            if ($("label[for='member_nickname'] > span.s_website_form_mark").length) {
                    $("label[for='member_nickname'] > span.s_website_form_mark").attr('style', '');
                }
        }
        else{
            this.$('input[name="member_nickname"]').prop('required', false);
            if ($("label[for='member_nickname'] > span.s_website_form_mark").length) {
                    $("label[for='member_nickname'] > span.s_website_form_mark").attr('style', 'display: none');
                }
        }
    },

});
