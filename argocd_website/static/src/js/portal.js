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
            }).then(function (healthy) {
                $el.removeClass(["fa-spin", "fa-circle-o-notch"]);
                if (healthy) {
                    $el.addClass(["fa-heart", "text-success"]);
                } else {
                    $el.addClass(["fa-times", "text-danger"]);
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

});
