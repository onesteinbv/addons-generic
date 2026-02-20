import publicWidget from "@web/legacy/js/public/public_widget";


// Simple health check good enough for simple users (use argocd for better insight)
publicWidget.registry.HealthCheck = publicWidget.Widget.extend({
    selector: ".o_portal_wrap .js_health_check",

    init: function () {
        this._super(...arguments)
        this.orm = this.bindService("orm");
    },

    start: function () {
        this._super();
        this.checkHealth();
    },

    checkHealth: function () {
        var $el = this.$el;
        var appId = $el.attr("data-app-id");

        this.orm.call("argocd.application", "check_health", [[parseInt(appId, 10)]]).then(function (healthStatuses) {
            $el.html("");
            for (var i in healthStatuses) {
                var $statusEl = $("<i class='fa fa-fw' />");
                if (healthStatuses[i]) {
                    $statusEl.addClass(["fa-heart", "text-success"]);
                } else {
                    $statusEl.addClass(["fa-times", "text-danger"]);
                }
                $el.append($statusEl);
            }
        });
    }
});

publicWidget.registry.PortalHomeCounters.include({
    /**
     * @override
     */
    _getCountersAlwaysDisplayed() {
        // We want to always show the applications entry
        return this._super(...arguments).concat(["app_count", "customer_count"]);
    },
});

publicWidget.registry.DomainCNAMECheck = publicWidget.Widget.extend({
    selector: ".o_portal_wrap .js_domain_cname_check",
    events: {
        "click button": "_onButtonClick",
        "keydown input": "_onKeyDown",
    },

    init: function () {
        this._super(...arguments)
        this.orm = this.bindService("orm");
    },

    start: function () {
        this._super();
        this.$input = this.$el.find("input");
        this.$validFeedback = this.$el.find(".text-success");
        this.$invalidFeedback = this.$el.find(".text-danger");
        this.$button = this.$el.find("button");
        this.$buttonIcon = this.$button.find("i");
        this.appId = parseInt(this.$el.attr("data-app-id"), 10);
        this.tagId = parseInt(this.$el.attr("data-tag-id"), 10);
        this.subdomain = this.$el.attr("data-subdomain");

        this.checkDomainCNAME();
    },

    _onButtonClick: function () {
        this.checkDomainCNAME();
    },

    _onKeyDown: function () {
        this.$input.removeClass("is-invalid");
        this.$input.removeClass("is-valid");
    },

    checkDomainCNAME: function () {
        var self = this;
        var domain = this.$input.val();

        if (!domain) {
            self.$input.removeClass("is-invalid");
            self.$input.removeClass("is-valid");
            self.$validFeedback.addClass("d-none");
            self.$invalidFeedback.addClass("d-none");
            return;
        }

        this.$button.attr("disabled", "disabled");
        this.$buttonIcon.removeClass("fa-check");
        this.$buttonIcon.addClass("spinner-grow");

        return this.orm.call(
            "argocd.application", "dns_cname_check", [this.appId, domain, this.tagId]
        ).then(function (res) {
            self.$validFeedback.toggleClass("d-none", !res);
            self.$invalidFeedback.toggleClass("d-none", res);
            self.$input.toggleClass("is-invalid", !res);
            self.$input.toggleClass("is-valid", res);
            self.$button.removeAttr("disabled");
            self.$buttonIcon.removeClass("spinner-grow");
            self.$buttonIcon.addClass("fa-check");
        }, function (err) {
            self.$invalidFeedback.html(err.message.data.message);
            self.$validFeedback.addClass("d-none");
            self.$invalidFeedback.removeClass("d-none");
            self.$input.removeClass("is-valid");
            self.$input.addClass("is-invalid");
            self.$button.removeAttr("disabled");
            self.$buttonIcon.removeClass("spinner-grow");
            self.$buttonIcon.addClass("fa-check");
        });
    }
});

publicWidget.registry.SignupForm = publicWidget.Widget.extend({
    selector: "form[action='/application/signup']",
    events: {
        "change input[name='target']": "_onTargetChange",
        "change select[name='customer_id']": "_onCustomerChange",
    },

    start: function () {
        this._super();
        this.$targetRadios = this.$el.find("input[name='target']");
        this.$customerSelection = this.$el.find(".js_customer_selection");
        this.$customerSelect = this.$el.find("select[name='customer_id']");

        // Initialize visibility based on current selection
        this._updateVisibility();
    },

    _onTargetChange: function () {
        this._updateVisibility();
    },

    _onCustomerChange: function () {
        this._updateVisibility();
    },

    _updateVisibility: function () {
        var target = this.$targetRadios.filter(":checked").val();

        // Show/hide customer selection dropdown
        if (target === "end_customer") {
            this.$customerSelection.show();
        } else {
            this.$customerSelection.hide();
        }
    }
});
