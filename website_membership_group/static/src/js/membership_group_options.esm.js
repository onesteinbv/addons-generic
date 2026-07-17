import {_t} from "@web/core/l10n/translation";
import options from "@web_editor/js/editor/snippets.options";
import {rpc} from "@web/core/network/rpc";

let _currentWrapEl = null;

/**
 * Helpers to filter for module-specific option classes.
 * Excludes base structural classes to prevent duplication in templates.
 */
function filterColClasses(classList) {
    const structuralCols = new Set(["mg_team_col", "mg_image_col", "mg_desc_col"]);
    const classes = (classList || "").split(/\s+/).filter((cls) => {
        if (structuralCols.has(cls)) return false;
        return (
            cls.startsWith("col-") ||
            cls.startsWith("order-") ||
            cls.startsWith("offset-") ||
            cls.startsWith("mg_")
        );
    });
    return Array.from(new Set(classes)).join(" ");
}

const filterMgClasses = (classList, excludeClass) => {
    return classList
        .split(/\s+/)
        .filter((cls) => cls.startsWith("mg_") && cls !== excludeClass)
        .join(" ");
};

/**
 * Adds/removes a single "flag" class from a class list depending on
 * whether it should currently be active, mirroring a checkbox-like
 * toggle.
 */
function _syncFlagClass(classList, flagClass, isActive) {
    const hasFlag = classList.includes(flagClass);
    if (isActive && !hasFlag) {
        return [...classList, flagClass];
    }
    if (!isActive) {
        return classList.filter((cls) => cls !== flagClass);
    }
    return classList;
}

/**
 * Computes the up-to-date class string for the members row, along with
 * whether the "single list" layout is active (needed afterwards to pick
 * the right team-column selector).
 */
function _computeMembersRowState(membersRow) {
    let membersClassesList = Array.from(
        new Set(
            (membersRow.className || "")
                .split(/\s+/)
                .filter((cls) => cls.startsWith("mg_") && cls !== "mg_members_row")
        )
    );

    const logosActivated = membersRow.classList.contains("mg_img_logos_layout");
    const singleListActivated = membersRow.classList.contains("mg_members_single_list");

    membersClassesList = _syncFlagClass(
        membersClassesList,
        "mg_img_logos_layout",
        logosActivated
    );
    membersClassesList = _syncFlagClass(
        membersClassesList,
        "mg_members_single_list",
        singleListActivated
    );

    return {
        membersClasses: membersClassesList.join(" "),
        singleListActivated,
    };
}

/**
 * Computes the filtered class strings for the team/image/description
 * columns, given the currently active layout.
 */
function _computeColumnClasses(wrapEl, headerRow, singleListActivated) {
    const activeTeamColSelector = singleListActivated
        ? ".mg_single_list_wrapper .mg_team_col"
        : ".mg_grouped_list_wrapper .mg_team_col";
    const teamCol =
        wrapEl.querySelector(activeTeamColSelector) ||
        wrapEl.querySelector(".mg_team_col");
    const imgCol = headerRow ? headerRow.querySelector(".mg_image_col") : null;
    const descCol = headerRow ? headerRow.querySelector(".mg_desc_col") : null;

    return {
        teamColClasses: teamCol ? filterColClasses(teamCol.className) : "",
        imgColClasses: imgCol ? filterColClasses(imgCol.className) : "",
        descColClasses: descCol ? filterColClasses(descCol.className) : "",
    };
}

/**
 * Reads (and clears) the pending "hidden member types" edit stored on the
 * wrap element's dataset. Returns null when there is nothing to apply.
 */
function _extractHiddenTypeIds(wrapEl) {
    if (!wrapEl.dataset || !wrapEl.dataset.hiddenTypes) {
        return null;
    }
    let hiddenIds = null;
    try {
        const parsed = JSON.parse(wrapEl.dataset.hiddenTypes);
        if (Array.isArray(parsed)) {
            hiddenIds = parsed;
        }
    } catch (e) {
        console.error("Error parsing dataset.hiddenTypes during save:", e);
    }
    delete wrapEl.dataset.hiddenTypes;
    wrapEl.removeAttribute("data-hidden-types");
    return hiddenIds;
}

/** Persists the computed values on the membership.group record. */
async function _persistMembershipGroup(groupId, writeVals) {
    try {
        await rpc("/web/dataset/call_kw", {
            model: "membership.group",
            method: "write",
            args: [[groupId], writeVals],
            kwargs: {},
        });
        console.log("Successfully saved changes to membership.group");
    } catch (error) {
        console.error("Failed to save changes to membership.group:", error);
    }
}

async function _saveMembershipGroupChanges() {
    const wrapEl = _currentWrapEl;
    if (!wrapEl || !wrapEl.isConnected) {
        return;
    }
    const groupId = parseInt(wrapEl.dataset.oeId, 10);
    if (!groupId) {
        return;
    }

    const membersRow = wrapEl.querySelector("#mg_members_row");
    const headerRow = wrapEl.querySelector("#mg_header_row");
    const wrapClasses = filterMgClasses(wrapEl.className, "mg_wrap");

    const {membersClasses, singleListActivated} = _computeMembersRowState(membersRow);
    const {teamColClasses, imgColClasses, descColClasses} = _computeColumnClasses(
        wrapEl,
        headerRow,
        singleListActivated
    );

    const writeVals = {
        website_snippet_wrap_classes: wrapClasses,
        website_snippet_members_classes: membersClasses,
        website_team_col_classes: teamColClasses,
        website_header_image_col_classes: imgColClasses,
        website_header_desc_col_classes: descColClasses,
    };

    const hiddenIds = _extractHiddenTypeIds(wrapEl);
    if (hiddenIds) {
        writeVals.website_hide_member_type_ids = [[6, 0, hiddenIds]];
    }

    await _persistMembershipGroup(groupId, writeVals);
}

function ensureGlobalSaveListener() {
    const parentDoc = window.parent ? window.parent.document : document;
    const saveBtn = parentDoc.querySelector(
        "button[data-action='save'], .o_we_website_top_actions button.btn-primary"
    );

    // Check if the button exists AND if it doesn't already have our custom flag
    if (saveBtn && !saveBtn.dataset.mgSaveBound) {
        saveBtn.addEventListener("mousedown", _saveMembershipGroupChanges, {
            capture: true,
        });

        // Stamp the button so we know it has been bound!
        saveBtn.dataset.mgSaveBound = "true";
    }
}
options.registry.MembershipGroupPage = options.Class.extend({
    init() {
        this._super(...arguments);
        _currentWrapEl = this.$target[0];
        this._hiddenTypesCache = undefined;
        ensureGlobalSaveListener();
        this.notification = this.bindService("notification");
    },
    destroy() {
        if (_currentWrapEl === this.$target[0]) {
            _currentWrapEl = null;
        }
        this._super(...arguments);
    },
    // eslint-disable-next-line no-unused-vars
    async _computeWidgetState(methodName, params) {
        if (methodName === "setHiddenTypes") {
            if (this._hiddenTypesCache !== undefined) return this._hiddenTypesCache;

            const groupId = parseInt(this.$target[0].dataset.oeId, 10);
            if (!groupId) return "";

            try {
                const groupData = await rpc("/web/dataset/call_kw", {
                    model: "membership.group",
                    method: "read",
                    args: [[groupId], ["website_hide_member_type_ids"]],
                    kwargs: {},
                });

                if (groupData && groupData.length > 0) {
                    const hiddenIds = groupData[0].website_hide_member_type_ids;
                    if (hiddenIds && hiddenIds.length > 0) {
                        const typeData = await rpc("/web/dataset/call_kw", {
                            model: "membership.group.member.type",
                            method: "search_read",
                            args: [[["id", "in", hiddenIds]], ["id", "name"]],
                            kwargs: {},
                        });
                        const widgetData = typeData.map((t) => ({
                            id: t.id,
                            display_name: t.name,
                        }));
                        this._hiddenTypesCache = JSON.stringify(widgetData);
                        return this._hiddenTypesCache;
                    }
                }
            } catch (e) {
                console.error(e);
            }

            this._hiddenTypesCache = "";
            return this._hiddenTypesCache;
        }
        return this._super(...arguments);
    },
    // eslint-disable-next-line no-unused-vars
    setHiddenTypes: function (previewMode, widgetValue, params) {
        if (previewMode) return;
        this._hiddenTypesCache =
            typeof widgetValue === "string" ? widgetValue : JSON.stringify(widgetValue);
        const parsedValue = JSON.parse(this._hiddenTypesCache);
        const typeIds = (Array.isArray(parsedValue) ? parsedValue : [])
            .map((item) => parseInt(item.id || item, 10))
            .filter((id) => !isNaN(id));
        this.$target[0].dataset.hiddenTypes = JSON.stringify(typeIds);
        this.notification.add(
            _t(
                "Hidden member types updated. Please save the changes for the changes to take effect."
            ),
            {type: "info", sticky: false}
        );
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
    },
});
