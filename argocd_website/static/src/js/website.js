odoo.define("argocd_website.website", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var { qweb } = require("web.core");

    publicWidget.registry.OrderAppProductConfigurator = publicWidget.Widget.extend({
        selector: ".js_order_app_product",
        events: {
            "change .js_order_app_attribute": "_onAttributeChange",
            "change .js_order_app_toggle": "_onToggleChange"
        },

        start: function () {
            this._super();
            this.productTemplateId = parseInt(this.$el.attr("data-id"), 10);
            this.$attributes = this.$el.find(".js_order_app_attribute");
        },

        _onAttributeChange: function () {
            // TODO: Look for available combinations, and change the other attribute selectors accordingly
            this._updateSubscriptionProduct();
        },

        _onToggleChange: function () {
            console.log(arguments);
        },

        _updateSubscriptionProduct: function() {
            var combination = this.$attributes.map(function () {
                return parseInt($(this).val(), 10);
            }).get();

            this._rpc({
                route: "/application/update_subscription_product",
                params: {
                    product_template_id: this.productTemplateId,
                    combination: combination
                }
            }).then(function () {
                // To be implemented
            });
        }
    });

    publicWidget.registry.OrderAppDetails = publicWidget.Widget.extend({
        selector: ".js_order_app_details",

        start: function () {
            this._super();
            this.$proceedBtn = this.$el.find(".js_order_app_proceed");
            this.$list = this.$el.find(".js_order_app_list");
            this.$loader = this.$el.find(".spinner-border");

            this.refreshSubscription();
        },

        refreshSubscription: function() {
            this.$loader.removeClass("d-none");
            this.$proceedBtn.addClass("d-none");
            this.$list.addClass("d-none");

            this._rpc({
                route: "/application/get_subscription_details"
            }).then(function (data) {
                var details = qweb.render(
                    "argo_website.List", {
                        sub: data
                    }
                );
                this.$list.html(details);

                this.$loader.addClass("d-none");
                this.$proceedBtn.removeClass("d-none");
                this.$list.removeClass("d-none");
            }.bind(this));

        }
    });

});
