/** @odoo-module **/
import dynamicSnippetCarouselOptions from "website.s_dynamic_snippet_carousel_options";
import options from "web_editor.snippets.options";
import utils from "web.utils";

options.registry.dynamic_project_list = dynamicSnippetCarouselOptions.extend({
    /**
     *
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.projectCategories = {};
        this.modelNameFilter = "project.project";
    },

    /**
     * @override
     */
    async willStart() {
        const _super = this._super.bind(this);
        await this._fetchProjectCategories();
        return _super(...arguments);
    },
    /**
     *
     * @override
     */
    async onBuilt() {
        this._super.apply(this, arguments);
        this.$target[0].dataset.snippet = 'dynamic_project_list';
    },

    _fetchProjectCategories: function () {
        return this._rpc({
            model: 'project.project.category',
            method: 'search_read',
            kwargs: {
                fields: ['id', 'name', "description"],
            }
        });
    },

    /**
     *
     * @override
     * @private
     */
    _renderCustomXML: async function (uiFragment) {
        // The parent _renderCustomXML function renders a filter and a template selector.
        await this._super.apply(this, arguments);
        await this._renderProjectCategorySelector(uiFragment);
    },

    _markupDictionary(obj) {
        Object.keys(obj).forEach(
            key => {obj[key] = typeof obj[key] === "string" ? utils.Markup(obj[key]) : obj[key]});
        return obj;
    },

    /**
     * Renders the project categories option selector content into the provided uiFragment.
     * @private
     * @param {HTMLElement} uiFragment
     */
    _renderProjectCategorySelector: async function (uiFragment) {
        const projectCategories = await this._fetchProjectCategories();
        for (const index in projectCategories) {
            this.projectCategories[projectCategories[index].id] = projectCategories[index];
        }
        const projectCategoriesSelectorEl = uiFragment.querySelector('[id="start_project_checkboxes"]');
        for (const id in this.projectCategories) {
            const checkbox = document.createElement('we-checkbox');
            console.log(id)
            console.log(this.projectCategories)
            console.log(projectCategoriesSelectorEl)
            checkbox.dataset.selectDataAttribute = JSON.stringify(
                this.projectCategories[id].id
                // This._markupDictionary(this.projectCategories[id])
            );
            checkbox.setAttribute('data-attribute-name','projectCategory_'+this.projectCategories[id].name.replace(/[^a-zA-Z0-9]/g,'_'))
            checkbox.setAttribute('string',this.projectCategories[id].name)
//            Checkbox.name=this.projectCategories[id].name
//            checkbox.string=this.projectCategories[id].name
//            button.innerText = this.projectCategories[id].name;
            projectCategoriesSelectorEl.after(checkbox);
        }
    },

    /**
     * @override
     * @private
     */
    _setOptionsDefaultValues: async function () {
        this._super.apply(this, arguments);

        this.options.wysiwyg.odooEditor.observerUnactive();
        this._setOptionValue('projectCategory', '');
        this.options.wysiwyg.odooEditor.observerActive();
    },

});

export default {
    DynamicProjectListOptions: options.registry.dynamic_project_list,
};
