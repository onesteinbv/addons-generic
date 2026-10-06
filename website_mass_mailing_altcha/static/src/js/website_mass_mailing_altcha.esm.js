import "@website_mass_mailing/js/website_mass_mailing";
import {Altcha} from "@website_altcha/altcha/altcha.esm";
import publicWidget from "@web/legacy/js/public/public_widget";
import {renderToString} from "@web/core/utils/render";
import {rpcBus} from "@web/core/network/rpc";

const SUBSCRIBE_ROUTE = "/website_mass_mailing/subscribe";

publicWidget.registry.subscribe.include({
    init: function () {
        this._super(...arguments);
        this._altcha = new Altcha();
    },

    willStart: async function () {
        this._altcha.loadLibs();
        return this._super(...arguments);
    },

    _updateSubscribeControlsStatus(isSubscriber) {
        this._super(...arguments);
        if (!isSubscriber && this._altcha._publicKey && window.top === window) {
            if (!this.el.parentElement.querySelector(".o_altcha_widget")) {
                $(renderToString("website_altcha.AltchaWidget", {})).insertAfter(
                    this.el.querySelector(".js_subscribe_wrap")
                );
            }
        }
    },

    _onSubscribeClick: async function () {
        const _super = this._super.bind(this);
        // The event is fired synchronously before the request is serialized
        const injectPayload = ({detail}) => {
            if (detail.url === SUBSCRIBE_ROUTE) {
                detail.data.params.altcha =
                    this.el.parentElement.querySelector('input[name="altcha"]')?.value;
            }
        };
        rpcBus.addEventListener("RPC:REQUEST", injectPayload);
        try {
            return await _super(...arguments);
        } finally {
            rpcBus.removeEventListener("RPC:REQUEST", injectPayload);
        }
    },
});
