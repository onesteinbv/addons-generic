import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MembershipGroupCollapsible = publicWidget.Widget.extend({
    selector: '#mg_members_row',

    start: function () {
        this.setupCollapsibleButtons();
        return this._super.apply(this, arguments);
    },

    setupCollapsibleButtons: function () {
        const buttons = this.el.querySelectorAll('.mg_collapse_btn');
        buttons.forEach(button => {
            button.onclick = (e) => {
                e.preventDefault();
                this.toggleDescription(button);
            };
        });
    },

    toggleDescription: function (button) {
        const descriptionId = button.getAttribute('aria-controls');
        // eslint-disable-next-line no-undef
        const description = document.getElementById(descriptionId);

        if (!description) return;

        const isExpanded = button.getAttribute('aria-expanded') === 'true';

        if (isExpanded) {
            description.classList.add('d-none');
            button.setAttribute('aria-expanded', 'false');
        } else {
            description.classList.remove('d-none');
            button.setAttribute('aria-expanded', 'true');
        }
    },
});
