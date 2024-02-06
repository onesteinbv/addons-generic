odoo.define("base_librecaptcha", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.captchaWidget = publicWidget.Widget.extend({
        selector: ".js_captcha",
        start: function () {
            this._super.apply(this, arguments);
            this._rpc({
                route: "/captcha"
            }).then(function (id) {
                this.$el.find("input[type='hidden']").val(id);
                this.$el.find("img")
                    .attr("src", _.str.sprintf("/captcha/media?id=%s", id))
                    .removeClass("d-none");
            }.bind(this));
        }
    });
});
