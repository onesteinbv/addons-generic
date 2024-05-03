/** @odoo-module **/
import DynamicSnippetCarousel from 'website.s_dynamic_snippet_carousel';

import publicWidget from "web.public.widget";

publicWidget.registry.dynamic_project_list = DynamicSnippetCarousel.extend({
    selector: '.s_dynamic_project_list',
    /**
     * Gets the category search domain
     *
     * @private
     * @returns Search domain
     */
    _getCategorySearchDomain: function() {
        const searchDomain = [];
        const filterByCategoryIds = JSON.parse(this.$el.get(0).dataset.filterByCategoryIds || '[]');
        if (filterByCategoryIds.length) {
            searchDomain.push(['category_id', 'in', filterByCategoryIds.map(projectCategory => projectCategory.id)]);
        }
        return searchDomain;
    },

    /**
     * Method to be overridden in child components in order to provide a search
     * domain if needed.
     * @override
     * @private
     */
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);
        searchDomain.push(...this._getCategorySearchDomain());
        return searchDomain;
    },
})


export default {
    DynamicProjectList: publicWidget.registry.dynamic_project_list,
};
