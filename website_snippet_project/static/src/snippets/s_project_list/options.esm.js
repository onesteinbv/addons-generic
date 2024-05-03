/** @odoo-module **/
import dynamicSnippetCarouselOptions from "website.s_dynamic_snippet_carousel_options";
import options from "web_editor.snippets.options";

options.registry.dynamic_project_list = dynamicSnippetCarouselOptions.extend({
    /**
     *
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = "project.project";
    },
    /**
     *
     * @override
     */
    async onBuilt() {
        this._super.apply(this, arguments);
        this.$target[0].dataset.snippet = 'dynamic_project_list';
    },
});

export default {
    DynamicProjectListOptions: options.registry.dynamic_project_list,
};
