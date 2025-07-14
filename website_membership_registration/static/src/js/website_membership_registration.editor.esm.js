import options from "@web_editor/js/editor/snippets.options";
import { rpc } from "@web/core/network/rpc";
const FILE_EXTENSIONS = ['.txt','.csv','.tsv','.jpg', '.jpeg', '.jpe', '.png', '.svg', '.gif','.pdf','.xls','.xlsx','.doc','.docx','.ppt','.pptx'];

options.registry.WebsiteMembershipRegistrationPage = options.Class.extend({
    /**
     * @override
     */
    start: function () {
        this.max_cv_file_size = parseInt(this.$target.closest('[data-max-cv-file-size]').data('max-cv-file-size'), 10);
        this.cv_file_formats = this.$target.closest('[data-cv-file-formats]').data('cv-file-formats');
        this.membership_group_style = this.$target.closest('[data-membership_group-style]').data('membership_group-style');
        return this._super.apply(this, arguments);
    },

    setMembershipGroupStyle: function (previewMode, widgetValue) {
        this.membership_group_style = widgetValue;
        rpc("/membership-registration/config/website", {
                        membership_registration_page_membership_group_style: this.membership_group_style,
        });
    },
    setMaxCvFileSize: function (previewMode, widgetValue) {
        const max_cv_file_size = parseInt(widgetValue, 10);
        if (!max_cv_file_size || max_cv_file_size < 1) {
            return false;
        }
        return rpc("/membership-registration/config/website", {
                        membership_registration_max_cv_file_size: max_cv_file_size,
        });
    },
    setFileFormats: function (previewMode, widgetValue) {
        if (widgetValue.trim() === "*") {
            this.cv_file_formats = widgetValue;
        }
        else{
            var supported_file_formats="";
            var file_formats = widgetValue.split(",");
            for (let i = 0; i < file_formats.length; i++) {
                var file_format = file_formats[i].trim().toLowerCase();
                if (FILE_EXTENSIONS.includes(file_format))
                {
                    supported_file_formats += (file_format +',');
                }
            }
            this.cv_file_formats = supported_file_formats.replace(/,\s*$/, "");
        }
        rpc("/membership-registration/config/website", {
                        membership_registration_cv_file_formats_supported: this.cv_file_formats,
        });
    },
    /**
     * @override
     */
    _computeWidgetState: function (methodName) {
        switch (methodName) {
            case 'setMembershipGroupStyle': {
                return this.membership_group_style;
            }
            case 'setMaxCvFileSize': {
                return this.max_cv_file_size;
            }
            case 'setFileFormats': {
                return this.cv_file_formats;
            }
        }
        return this._super(...arguments);
    },
    _computeWidgetVisibility: function (widgetName) {
        if (widgetName === 'cv_options') {
            return this.$target[0].querySelector('#div_cv')
        }
        return this._super.apply(this, arguments);
    },
});
