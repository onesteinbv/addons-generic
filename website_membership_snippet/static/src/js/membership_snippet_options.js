/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import dynamicSnippetOptions from "@website/snippets/s_dynamic_snippet/options";
import { rpc } from "@web/core/network/rpc";

const dynamicSnippetMembersOptions = dynamicSnippetOptions.extend({
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = "res.partner";
        this.groups = {};
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _computeWidgetVisibility: function (widgetName, params) {
        return this._super.apply(this, arguments);
    },
    /**
     * Fetches published membership groups.
     * @private
     * @returns {Promise}
     */
    _fetchGroups: function () {
        return rpc("/membership/snippet/groups");
    },
    /**
     * @override
     * @private
     */
    _renderCustomXML: async function (uiFragment) {
        await this._super.apply(this, arguments);
        await this._renderGroupSelector(uiFragment);
    },
    /**
     * Renders the group option selector content into the provided uiFragment.
     * @private
     * @param {HTMLElement} uiFragment
     */
    _renderGroupSelector: async function (uiFragment) {
        if (!Object.keys(this.groups).length) {
            const groupsList = await this._fetchGroups();
            this.groups = {};
            for (let index in groupsList) {
                this.groups[groupsList[index].id] = groupsList[index];
            }
        }
        const groupSelectorEl = uiFragment.querySelector('[data-name="group_opt"]');
        return this._renderSelectUserValueWidgetButtons(groupSelectorEl, this.groups);
    },
    /**
     * Sets default options values.
     * @override
     * @private
     */
    _setOptionsDefaultValues: function () {
        this._setOptionValue("filterByGroupId", -1);
        this._super.apply(this, arguments);
    },
});

options.registry.dynamic_snippet_members = dynamicSnippetMembersOptions;

export default dynamicSnippetMembersOptions;
