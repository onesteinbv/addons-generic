/** @odoo-module */
/* Copyright 2023 Onestein - Anjeel Haria
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {FormController} from "@web/views/form/form_controller";
import {patch} from "@web/core/utils/patch";

// Patch FormController to always load attachment alongwith the chatter on the side bar
patch(FormController.prototype, "web_responsive_disable_form_attachment_preview.FormController", {
    setup() {
        this._super();
        this.hasAttachmentViewerInArch = true;
    },
});
