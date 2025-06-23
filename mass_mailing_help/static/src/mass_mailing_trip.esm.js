import {doAction, wait, waitUntilAvailable} from "@web_help/helpers.esm";
import {Trip} from "@web_help/trip.esm";
import {markup} from "@odoo/owl";
import {registry} from "@web/core/registry";
import { user } from "@web/core/user";
import { _t } from "@web/core/l10n/translation";

export class MassMailingTrip extends Trip {
    setup() {
        this.addStep({
            selector: ".o_list_button_add, .o-kanban-button-new",
            content: _t("First lets create a new mailing."),
        });

        this.addStep({
            selector: ".o_cell:has(input#subject_0), .o_cell:has(label[for='subject_0'])",
            content: _t("Choose a nice descriptive subject."),
            beforeHighlight: async () => {
                // Use switch view here
                $(".o_list_button_add, .o-kanban-button-new").click();
                await waitUntilAvailable(".o_form_view_container input#subject_0");
            },
            padding: 2
        });

        this.addStep({
            selector: "div[name='mailing_model_id'], li.ui-menu-item",
            content: _t(
                "There are different methods of sending mailings. But for " +
                "now we're focussing on using mailing lists. This gives the ability " +
                "for recepients to unsubscribe / subscribe to mailing lists they find " +
                "interesting. Mailing lists are also integrated into the Website app."
            ),
            beforeHighlight: async () => {
                $("div[name='mailing_model_id'] input").click();
                await wait(750);
            }
        });

        this.addStep({
            selector: "div.o_mass_mailing_contact_list_ids",
            content: _t(
                "Select here your mailing list, but since we don't have one we will create one."
            )
        });

        this.addStep({
            selector: "[data-menu-xmlid='mass_mailing.menu_email_mass_mailing_lists']",
            content: markup(_t(
                "To create a new mailing list go to <b>Email Marketing > Mailing Lists > Mailing Lists</b>."
            )),
            beforeHighlight: async () => {
                this.env.services.ui.activateElement(".o_menu_sections");
                $("[data-menu-xmlid='mass_mailing.mass_mailing_mailing_list_menu']").click();
                await waitUntilAvailable("[data-menu-xmlid='mass_mailing.menu_email_mass_mailing_lists']");
                this.env.services.ui.deactivateElement(".o_menu_sections");
            }
        });

        this.addStep({
            selector: ".o_list_button_add, .o-kanban-button-new",
            content: _t(
                "Click on the Create button."
            ),
            beforeHighlight: async () => {
                await doAction("mass_mailing.action_view_mass_mailing_lists", {clearBreadcrumbs: true});
                await waitUntilAvailable(".o_list_button_add, .o-kanban-button-new");
            }
        });

        this.addStep({
            selector: ".o_cell:has(input#is_public_0), .o_cell:has(label[for='is_public_0'])",
            content: _t(
                "Make sure to enable 'Show In Preferences' this allows the recipient to unsubscribe " +
                "from the mailing list using the website (in EU this is required by the GDPR)."
            ),
            beforeHighlight: async () => {
                $(".o_list_button_add, .o-kanban-button-new").click();
                await waitUntilAvailable(".o_cell:has(input#is_public_0)");
            }
        });

        this.addStep({
            selector: "button[name='action_view_contacts']",
            content: _t(
                "once create created we want to add some contacts to this mailing list. " +
                "The easiest way to do this is to click on the 'Recipients' button here."
            ),
            beforeHighlight: async () => {
                await doAction("mass_mailing.action_view_mass_mailing_lists", {viewType: "form"});
                await waitUntilAvailable("button[name='action_view_contacts']");
            }
        });

        this.addStep({
            selector: ".o_list_button_add, .o-kanban-button-new",
            content: _t(
                "Lets add a Recipient."
            ),
            beforeHighlight: async () => {
                await doAction("mass_mailing.action_view_mass_mailing_contacts");
                await waitUntilAvailable(".o_list_button_add, .o-kanban-button-new");
            }
        });

        this.addStep({
            selector: ".o_cell:has(input#partner_id_0), .o_cell:has(label[for='partner_id_0'])",
            content: _t(
                "The best way to do this is to link it to a contact (from the Contacts app) " +
                "to prevent duplicated information. This is optional, if your business contacts " +
                "and marketing contacts are totally separate you don't have to do it."
            ),
            beforeHighlight: async () => {
                $(".o_list_button_add, .o-kanban-button-new").click();
                await waitUntilAvailable(".o_form_view_container .o_cell:has(input#partner_id_0)");
            }
        });

        this.addStep({
            selector: "[data-menu-xmlid='mass_mailing.mass_mailing_menu']",
            content: _t(
                "Once you're done adding recipients lets go back and create the actual mailing."
            )
        });

        this.addStep({
            selector: ".wysiwyg_iframe",
            content: _t(
                "You can create a plain text or design a mailing using building blocks." +
                "We recommend the latter as it results in more clicks."
            ),
            beforeHighlight: async () => {
                await doAction("mass_mailing.mailing_mailing_action_mail", {viewType: "form"});
                await waitUntilAvailable(".wysiwyg_iframe");
            }
        });
        if (odoo.debug) {
            this.addStep({
                selector: ".o_notebook_headers li:nth-child(2)",
                content: _t(
                    "Use A/B testing to optimize your mailing"
                )
            });
        }

        this.addStep({
            selector: "button[name='action_test']",
            content: _t(
                "You can send a test mail to yourself by clicking 'Test'."
            )
        });

        this.addStep({
            selector: ".o_control_panel_actions",
            content: markup(_t(
                "After sending the mailing you can find handy information about it on top of the form here. " +
                "<b>This is now invisible but once sent it will popup here</b>."
            )),
        });

        this.addStep({
            selector: ".js_web_help_btn",
            content: _t(
                "This is the end. You can always open this tutorial again by clicking the '?' button."
            ),
            beforeHighlight: async () => {
                await doAction("mass_mailing.mailing_mailing_action_mail", {clearBreadcrumbs: true});
                await waitUntilAvailable(".js_web_help_btn:not(.d-none)");
            }
        });
    }
}

registry.category("trips").add("mass_mailing_trip", {
    Trip: MassMailingTrip,
    selector: async (model, viewType) => {
        const isErpManager = await user.hasGroup("base.group_erp_manager");
        return model === "mailing.mailing" && ["list", "kanban"].includes(viewType) && (odoo.debug && isErpManager || !isErpManager);
    }
});
