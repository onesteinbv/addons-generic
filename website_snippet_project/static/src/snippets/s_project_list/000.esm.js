/** @odoo-module **/
import DynamicSnippetCarousel from 'website.s_dynamic_snippet_carousel';

import publicWidget from "web.public.widget";

publicWidget.registry.dynamic_project_list = DynamicSnippetCarousel.extend({
    selector: '.s_dynamic_project_list',

    /**
     * Parses the project category information from the data attributes
     *
     * @private
     * @returns Parsed JSON object
     */
    _parseCategoryData: function() {
        const projectCategoryData = this.$el.get(0).dataset.projectCategory;
        if (!projectCategoryData)
            return {id: "all", name: "", description: ""};
        return JSON.parse(projectCategoryData);
    },

    /**
     * Gets the category search domain
     *
     * @private
     * @returns Search domain
     */
    _getCategorySearchDomain: function() {
        const searchDomain = [];
        const projectCategory = this._parseCategoryData();
        if (projectCategory.id === "all") {
            return searchDomain;
        }
        if (projectCategory.id) {
            searchDomain.push(['category_id', '=', projectCategory.id]);
        }
        return searchDomain;
    },

    /**
     * @override
     * @private
     */
    _renderContent: function () {
        const result = this._super.apply(this, arguments);

        const projectCategory = this._parseCategoryData();
        const $title = this.$el.find('h3');
        const $subTitle = this.$el.find('h4');
        const $templateArea = this.$el.find('.dynamic_snippet_template');

        this.trigger_up('widgets_stop_request', {
            $target: $templateArea,
        });
        $title.text(projectCategory.name || "");
        $subTitle.text(projectCategory.description || "");
        this.trigger_up('widgets_start_request', {
            $target: $templateArea,
            editableMode: this.editableMode,
        });

        return result;
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
