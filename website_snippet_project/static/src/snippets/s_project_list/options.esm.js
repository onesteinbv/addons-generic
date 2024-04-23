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
        this.tagIDs = JSON.parse(this.$target[0].dataset.filterByTagIds || '[]');
        const tags = await this._rpc({
            model: 'project.project.category',
            method: 'search_read',
            domain: [['website_published', '=', true]],
            fields: ['id', 'display_name'],
        });

        this.allTagsByID = {};
        for (const tag of tags) {
            this.allTagsByID[tag.id] = tag;
        }
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

    async _fetchProjectCategories() {
        this.tagIDs = JSON.parse(this.$target[0].dataset.filterByTagIds || '[]');
        const tags = await this._rpc({
            model: 'project.project.category',
            method: 'search_read',
            domain: [['website_published', '=', true]],
            fields: ['id', 'display_name'],
        });

        this.allTagsByID = {};
        for (const tag of tags) {
            this.allTagsByID[tag.id] = tag;
        }
        return this._rpc({
            model: 'project.project.category',
            method: 'search_read',
            domain: [['website_published', '=', true]],
            fields: ['id', 'display_name'],
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
   },


    _markupDictionary(obj) {
        Object.keys(obj).forEach(
            key => {obj[key] = typeof obj[key] === "string" ? utils.Markup(obj[key]) : obj[key]});
        return obj;
    },


    setTags(previewMode, widgetValue, params) {
        this.tagIDs = JSON.parse(widgetValue).map(tag => tag.id);
        this.selectDataAttribute(previewMode, JSON.stringify(this.tagIDs), params);
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

    async _computeWidgetState(methodName, params) {
        if (methodName === 'setTags') {
            return JSON.stringify(this.tagIDs.map(id => this.allTagsByID[id]));
        }
        return this._super(...arguments);
    },

});

export default {
    DynamicProjectListOptions: options.registry.dynamic_project_list,
};
