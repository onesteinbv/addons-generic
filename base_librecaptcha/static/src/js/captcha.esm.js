import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.captchaWidget = publicWidget.Widget.extend({
    selector: ".js_captcha",
    start: function () {
        this._super.apply(this, arguments);
        rpc("/captcha").then(
            function (id) {
                this.$el.find("input[type='hidden']").val(id);
                this.$el
                    .find("img")
                    .attr("src", `/captcha/media?id=${id}`)
                    .removeClass("d-none");
            }.bind(this)
        );
    },
});
