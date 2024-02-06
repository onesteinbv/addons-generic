/** @odoo-module **/
import {doAction, wait, waitUntilAvailable} from "@web_help/helpers.esm";
import {Trip} from "@web_help/trip.esm";
import {registry} from "@web/core/registry";
import session from "web.session";

export class MassMailingTripNoDebug extends Trip {
    setup() {
        this.addStep({
            selector: "a[data-menu-xmlid='base.menu_administration']",
            content: this.env._t(
                "First make sure you're in developer mode to make sure you have all " +
                "options available. You can turn this on by going to the general settings " +
                "from there scroll completely down and click 'Activate the developer mode'."
            ),
            beforeHighlight: async () => {
                $(".o_navbar_apps_menu > button").click();
                await waitUntilAvailable("a[data-menu-xmlid='base.menu_administration']");
            }
        });

        this.addStep({
            selector: "#developer_tool",
            content: this.env._t("Once activated return to the Email Marketing app and click the '?' button again."),
            beforeHighlight: async () => {
                await doAction("base_setup.action_general_configuration", {clearBreadcrumbs: true});
                await waitUntilAvailable(".settings");
                $(".settings").animate({
                    scrollTop: $(".app_settings_block:not(.o_hidden)").height()
                }, 750);
                await wait(775);
            }
        });

    }
}

registry.category("trips").add("mass_mailing_no_debug_trip", {
    Trip: MassMailingTripNoDebug,
    selector: async (model, viewType) => {
        const isErpManager = await session.user_has_group("base.group_erp_manager");
        return model === "mailing.mailing" && ["list", "kanban"].includes(viewType) && !odoo.debug && isErpManager;
    }
});
