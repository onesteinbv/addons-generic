import options from "@web_editor/js/editor/snippets.options";
import {rpc} from "@web/core/network/rpc";
/**
 * Helper to filter for module-specific option classes.
 * Excludes base structural classes to prevent duplication in templates.
 */
const filterMgClasses = (classList, excludeClass) => {
    return classList
        .split(/\s+/)
        .filter((cls) => cls.startsWith("mg_") && cls !== excludeClass)
        .join(" ");
};
options.registry.MembershipGroupPage = options.Class.extend({
    /**
     * @override
     */
    // eslint-disable-next-line no-unused-vars
    selectClass: function (previewMode, widgetValue, params) {
        this._super(...arguments);
        // Only save to database on actual click (not during hover preview)
        if (!previewMode) {
            this._saveToDatabase();
        }
    },

    /**
     * Save the current class list to the database
     */
    _saveToDatabase: function () {
        const id = parseInt(this.$target[0].dataset.oeId, 10);
        // Filter to keep only option classes, excluding 'mg_wrap'
        const classes = filterMgClasses(this.$target[0].className, "mg_wrap");
        if (this.lastSavedClasses !== classes) {
            this.lastSavedClasses = classes;
            if (id && classes) {
                return rpc("/web/dataset/call_kw", {
                    model: "membership.group",
                    method: "write",
                    args: [[id], {website_snippet_wrap_classes: classes}],
                    kwargs: {},
                });
            }
        }
    },
});

options.registry.MemberLayoutOpts = options.Class.extend({
    /**
     * @override
     * Triggered for Layout and Description toggles.
     */
    // eslint-disable-next-line no-unused-vars
    selectClass: function (previewMode, value, $li) {
        this._super(...arguments);
        const cards = this.$target[0].querySelectorAll(".mg_member_item.mg_has_desc");
        const isCollapsible = this.$target.hasClass("mg_collapse_desc");

        cards.forEach((card) => {
            const descId = card.getAttribute("data-target-desc");
            const desc = descId ? this.$target[0].querySelector(`#${descId}`) : null;
            const icon = card.querySelector(".mg_accordion_indicator i");

            // Strip active expansion styles
            card.classList.remove("mg_accordion_expanded");

            // Reset chevron to point down
            if (icon) {
                icon.classList.remove("fa-chevron-up");
                icon.classList.add("fa-chevron-down");
            }

            // Instantly hide or show the description blocks based on the checkbox state
            if (desc) {
                if (isCollapsible) {
                    desc.classList.add("d-none");
                    icon.classList.remove("d-none");
                } else {
                    desc.classList.remove("d-none");
                    icon.classList.add("d-none");
                }
            }
        });
        if (!previewMode) {
            this._saveToDatabase();
        }
    },

    _saveToDatabase: function () {
        const id = parseInt(this.$target[0].dataset.oeId, 10);
        // Filter to keep only option classes, excluding 'mg_members_row'
        const classes = filterMgClasses(this.$target[0].className, "mg_members_row");

        if (this.lastSavedClasses !== classes) {
            this.lastSavedClasses = classes;
            if (id && classes) {
                return rpc("/web/dataset/call_kw", {
                    model: "membership.group",
                    method: "write",
                    args: [[id], {website_snippet_members_classes: classes}],
                    kwargs: {},
                });
            }
        }
    },
});

options.registry.MemberColOpts = options.Class.extend({
    start: function () {
        const self = this;
        this._super(...arguments);

        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === "class") {
                    self._saveToDatabase();
                }
            });
        });

        this.observer.observe(this.$target[0], {
            attributes: true,
            attributeFilter: ["class"],
        });
    },

    destroy: function () {
        if (this.observer) {
            this.observer.disconnect();
        }
        this._super(...arguments);
    },

    _saveToDatabase: function () {
        const $row = this.$target.closest("#mg_members_row");
        const id = parseInt($row[0]?.dataset.oeId, 10);
        const classes = this.$target[0].className
            .split(/\s+/)
            .filter((cls) => cls.startsWith("mg_") || cls.startsWith("col-"))
            .join(" ");

        const field = this.$target.hasClass("mg_committee_col")
            ? "website_committee_col_classes"
            : "website_team_col_classes";

        if (id && field && classes) {
            if (this.lastSavedColClasses !== classes) {
                this.lastSavedColClasses = classes;
                return rpc("/web/dataset/call_kw", {
                    model: "membership.group",
                    method: "write",
                    args: [[id], {[field]: classes}],
                    kwargs: {},
                });
            }
        }
    },
});

options.registry.MembershipGroupPageHeaderOpts = options.Class.extend({
    start: function () {
        const self = this;
        this._super(...arguments);

        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === "class") {
                    self._saveToDatabase();
                }
            });
        });

        this.observer.observe(this.$target[0], {
            attributes: true,
            attributeFilter: ["class"],
        });
    },

    destroy: function () {
        if (this.observer) {
            this.observer.disconnect();
        }
        this._super(...arguments);
    },

    _saveToDatabase: function () {
        const $row = this.$target.closest("#mg_header_row");
        const id = parseInt($row[0]?.dataset.oeId, 10);
        const classes = this.$target[0].className
            .split(/\s+/)
            .filter(
                (cls) =>
                    cls.startsWith("col-") ||
                    cls.startsWith("order-") ||
                    cls.startsWith("offset-")
            )
            .join(" ");

        const field = this.$target.hasClass("mg_image_col")
            ? "website_header_image_col_classes"
            : "website_header_desc_col_classes";

        if (id && field && classes) {
            if (this.lastSavedColClasses !== classes) {
                this.lastSavedColClasses = classes;
                return rpc("/web/dataset/call_kw", {
                    model: "membership.group",
                    method: "write",
                    args: [[id], {[field]: classes}],
                    kwargs: {},
                });
            }
        }
    },
});
