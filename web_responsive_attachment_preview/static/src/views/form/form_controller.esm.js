/** @odoo-module */
/* Copyright 2025 Onestein - Anjeel Haria
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import { patch, unpatch } from "@web/core/utils/patch";
import {FormController} from "@web/views/form/form_controller";

// Undo web_responsive's patch
unpatch(FormController.prototype, "web_responsive.FormController");

// Patch FormController to load attachment automatically alongwith the chatter on the side bar based on user preference
patch(FormController.prototype, "web_responsive_attachment_preview.FormController", {
    setup() {
        this._super();
        this.hasAttachmentViewerInArch =
            this.hasAttachmentViewerInArch && odoo.auto_attachment_preview === "yes";
    },
});
