import options from "@web_editor/js/editor/snippets.options";
import s_dynamic_snippet_carousel_options from "@website/snippets/s_dynamic_snippet_carousel/options";

options.registry.dynamic_project_list = s_dynamic_snippet_carousel_options.extend({
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
        this.$target[0].dataset.snippet = "s_dynamic_project_list";
    },
});

export default {
    DynamicProjectListOptions: options.registry.dynamic_project_list,
};
