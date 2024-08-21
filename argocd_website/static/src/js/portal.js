odoo.define("argocd_website.portal", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var rpc = require("web.rpc");

    // Simple health check good enough for simple users (use argocd for better insight)
    publicWidget.registry.HealthCheck = publicWidget.Widget.extend({
        selector: ".o_portal_wrap .js_health_check",

        start: function () {
            this._super();
            this.checkHealth();
        },

        checkHealth: function () {
            var $el = this.$el;
            var appId = $el.attr("data-app-id");

            rpc.query({
                model: "argocd.application",
                method: "check_health",
                args: [parseInt(appId, 10)]
            }).then(function (healthStatuses) {
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
            return this._super(...arguments).concat(["app_count"]);
        },
    });

    publicWidget.registry.DomainCNAMECheck = publicWidget.Widget.extend({
        selector: ".o_portal_wrap .js_domain_cname_check",
        events: {
            "click button": "_onButtonClick",
            "keydown input": "_onKeyDown",
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

            return rpc.query({
                model: "argocd.application",
                method: "dns_cname_check",
                args: [this.appId, domain, this.tagId]
            }).then(function (res) {
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

});
