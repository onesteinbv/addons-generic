/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import { rpc } from "@web/core/network/rpc";

options.registry.MembershipSnippetOptions = options.Class.extend({
    /**
     * @override
     */
    async _renderCustomXML(uiFragment) {
        await this._super(...arguments);
        const groups = await this._fetchGroups();
        this._renderGroupSelector(uiFragment, groups);
    },

    /**
     * @private
     */
    async _fetchGroups() {
        try {
            return await rpc("/membership/snippet/groups");
        } catch (error) {
            console.error("Failed to fetch groups:", error);
            return [];
        }
    },

    /**
     * @private
     */
    _renderGroupSelector(uiFragment, groups) {
        const selectEl = uiFragment.querySelector('[data-name="group_id_opt"]');
        if (!selectEl || !groups.length) {
            return;
        }

        // Remove existing buttons
        selectEl.querySelectorAll('we-button').forEach(btn => btn.remove());

        // Add group options directly to we-select (same pattern as dynamic snippets)
        groups.forEach(group => {
            const button = document.createElement('we-button');
            button.dataset.selectDataAttribute = group.id;
            button.textContent = group.name;
            selectEl.appendChild(button);
        });
    },
});

export default options.registry.MembershipSnippetOptions;