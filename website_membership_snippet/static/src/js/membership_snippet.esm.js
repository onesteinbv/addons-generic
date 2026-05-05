/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import DynamicSnippet from "@website/snippets/s_dynamic_snippet/000";

const DynamicSnippetMembers = DynamicSnippet.extend({
    selector: ".s_dynamic_snippet_members",
    disabledInEditableMode: false,

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);
        const filterByGroupId = parseInt(this.$el.get(0).dataset.filterByGroupId);
        if (filterByGroupId >= 0) {
            searchDomain.push(
                ["membership_group_member_ids.group_id", "=", filterByGroupId],
                ["membership_group_member_ids.state", "=", "current"]
            );
        }
        return searchDomain;
    },
    /**
     * @override
     * @private
     */
    _getMainPageUrl() {
        return "/members";
    },
});

publicWidget.registry.dynamic_snippet_members = DynamicSnippetMembers;

export default DynamicSnippetMembers;
