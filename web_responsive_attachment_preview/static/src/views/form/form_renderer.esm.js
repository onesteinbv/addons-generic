/* Copyright 2025 Onestein - Anjeel Haria
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {FormRenderer} from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";
import {unpatchDisableFilePreview} from "@web_responsive/views/form/form_renderer.esm";

// Undo web_responsive's patch
unpatchDisableFilePreview();

// Patch FormController to load attachment alongwith the chatter on the side bar based on user preference
export const patchFilePreview = patch(FormRenderer.prototype, {
    /** @returns {Boolean}*/
    hasFile() {
        const res = super.hasFile();
        return res && odoo.auto_attachment_preview === "yes";
    },
});
