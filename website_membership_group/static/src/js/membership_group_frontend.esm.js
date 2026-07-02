import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MembershipGroupCollapsible = publicWidget.Widget.extend({
    selector: "#mg_members_row",
    events: {
        "click .mg_member_item.mg_has_desc": "_onCardClick",
    },
    _onCardClick: function (e) {
        if (!this.el.classList.contains("mg_collapse_desc")) {
            return;
        }
        if (e.target.closest(".mg_clickable_link")) {
            return;
        }

        e.preventDefault();
        this.toggleAccordion(e.currentTarget);
    },

    toggleAccordion: function (card) {
        const descriptionId = card.getAttribute("data-target-desc");
        if (!descriptionId) return;

        const description = this.el.querySelector(`#${descriptionId}`);
        const chevronIcon = card.querySelector(".mg_accordion_indicator i");

        if (!description) return;

        const isHidden = description.classList.contains("d-none");

        if (isHidden) {
            description.classList.remove("d-none");
            card.classList.add("mg_accordion_expanded");

            if (chevronIcon) {
                chevronIcon.classList.remove("fa-chevron-down");
                chevronIcon.classList.add("fa-chevron-up");
            }
        } else {
            description.classList.add("d-none");
            card.classList.remove("mg_accordion_expanded");

            if (chevronIcon) {
                chevronIcon.classList.remove("fa-chevron-up");
                chevronIcon.classList.add("fa-chevron-down");
            }
        }
    },
});
