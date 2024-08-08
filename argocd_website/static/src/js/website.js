odoo.define("argocd_website.website", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var { SIZES, uiService } = require('@web/core/ui/ui_service');
    var { qweb } = require("web.core");
    require("website.content.menu");

    publicWidget.registry.OrderAppProductConfigurator = publicWidget.Widget.extend({
        selector: ".js_order_app_product",
        events: {
            "change select.js_order_app_attribute": "_onAttributeChange",
            "change .js_order_app_attribute input": "_onAttributeChange",
            "change .js_order_app_toggle": "_onToggleChange",
            "click .js_order_app_product_header": "_onClickHeader"
        },

        init: function (websiteRoot) {
            this._super.apply(this, arguments);
            this._websiteRoot = websiteRoot;
        },

        start: function () {
            this._super.apply(this, arguments);
            this.productTemplateId = parseInt(this.$el.attr("data-id"), 10);
            this.$attributes = this.$el.find(".js_order_app_attribute");
            this.$toggle = this.$el.find(".js_order_app_toggle");
            this.$header = this.$el.find(".js_order_app_product_header");
        },

        _isActive: function () {
            if (!this.$toggle.length) return true;
            return this.$toggle.is(":checked");
        },

        _onClickHeader: function (ev) {
            if (ev.target.nodeName === "INPUT") return;
            this.$toggle.click();
        },

        _onAttributeChange: function () {
            // TODO: Look for available combinations, and change the other attribute selectors accordingly
            if (!this._isActive()) return;
            this._updateSubscriptionProduct();
        },

        _onToggleChange: function () {
            if (this._isActive()) {
                this._updateSubscriptionProduct();
                this.$header.addClass("bg-light");
            } else {
                this._removeSubscriptionProduct();
                this.$header.removeClass("bg-light");
            }
        },

        _removeSubscriptionProduct: function () {
            return this._rpc({
                route: "/application/remove_subscription_product",
                params: {
                    product_template_id: this.productTemplateId
                }
            }).then(function () {
                this._websiteRoot.trigger("refreshSubscription");
            }.bind(this));
        },

        _updateSubscriptionProduct: function() {
            var combination = this.$attributes.map(function () {
                var $el = $(this);
                var valueId = null;
                if ($el.is("select")) {
                    valueId = $el.val();
                } else {
                    valueId = $el.find(":checked").val();
                }
                return parseInt(valueId, 10);
            }).get();

            return this._rpc({
                route: "/application/update_subscription_product",
                params: {
                    product_template_id: this.productTemplateId,
                    combination: combination
                }
            }).then(function () {
                this._websiteRoot.trigger("refreshSubscription");
            }.bind(this));
        }
    });

    publicWidget.registry.OrderAppDetails = publicWidget.Widget.extend({
        selector: ".js_order_app_details",

        init: function (websiteRoot) {
            this._super.apply(this, arguments);
            this._websiteRoot = websiteRoot;
        },

        start: function () {
            this._super();
            this.$proceedBtn = this.$el.find(".js_order_app_proceed");
            this.$list = this.$el.find(".js_order_app_list");
            this.$loader = this.$el.find(".spinner-border");

            this.refreshSubscription();
            this._websiteRoot.on("refreshSubscription", this, this.refreshSubscription);
        },

        refreshSubscription: function () {
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
                this.$proceedBtn.toggleClass("disabled", !data.lines.length);
            }.bind(this));
        }
    });

    var UpdateOrderDetailsPaddingMixin = {
        start: function () {
            var res = this._super(...arguments);
            this.$orderDetails = this.$main.find(".js_order_app_details");
            return res;
        },

        _updateMainPaddingTop: function () {
            var isLarge = uiService.getSize() >= SIZES.LG;
            this.$orderDetails.css("padding-top", this.fixedHeader && this._isShown() && isLarge ? this.headerHeight : "");
            return this._super(...arguments);
        }
    };

    publicWidget.registry.StandardAffixedHeader.include(UpdateOrderDetailsPaddingMixin)

    publicWidget.registry.FixedHeader.include(UpdateOrderDetailsPaddingMixin);

});
