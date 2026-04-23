/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.MembershipSnippet = publicWidget.Widget.extend({
    selector: ".s_membership_members",
    
    async start() {
        await this._super(...arguments);
        const groupId = parseInt(this.el.dataset.groupId, 10);
        if (groupId) {
            await this._loadMembers(groupId);
        }
    },
    
    async _loadMembers(groupId) {
        try {
            const members = await rpc("/membership/snippet/members", {
                group_id: groupId,
            });
            this._renderMembers(members);
        } catch (error) {
            console.error("Failed to load members:", error);
        }
    },
    
    _renderMembers(members) {
        const container = this.el.querySelector(".s_membership_members_container");
        if (!container || !members.length) {
            this.el.classList.add("o_snippet_empty");
            return;
        }
        
        const layout = this.el.dataset.layout || "grid";
        let html = "";
        
        if (layout === "list") {
            html = this._renderList(members);
        } else if (layout === "avatars") {
            html = this._renderAvatars(members);
        } else {
            html = this._renderGrid(members);
        }
        
        container.innerHTML = html;
        this.el.classList.remove("o_snippet_empty");
    },
    
    _renderGrid(members) {
        return `<div class="row g-3">${members.map(m => `
            <div class="col-md-4 col-lg-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <img class="rounded-circle mb-3" 
                             style="width: 80px; height: 80px; object-fit: cover;"
                             src="${m.image || "/web/static/img/user_placeholder.jpg"}" 
                             alt="${m.name}"/>
                        <h5 class="card-title">${m.name}</h5>
                        ${m.description ? `<p class="card-text text-muted small">${m.description}</p>` : ""}
                        ${m.url ? `<a href="${m.url}" class="btn btn-sm btn-primary">View Profile</a>` : ""}
                    </div>
                </div>
            </div>
        `).join("")}</div>`;
    },
    
    _renderList(members) {
        return `<div class="row">${members.map(m => `
            <div class="col-12 mb-3">
                <div class="d-flex align-items-center gap-3 p-3 bg-light rounded">
                    <img class="rounded-circle" 
                         style="width: 60px; height: 60px; object-fit: cover;"
                         src="${m.image || "/web/static/img/user_placeholder.jpg"}" 
                         alt="${m.name}"/>
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${m.name}</h6>
                        ${m.description ? `<small class="text-muted">${m.description}</small>` : ""}
                    </div>
                    ${m.url ? `<a href="${m.url}" class="btn btn-sm btn-outline-primary">View</a>` : ""}
                </div>
            </div>
        `).join("")}</div>`;
    },
    
    _renderAvatars(members) {
        return `<div class="d-flex flex-wrap justify-content-center gap-3">${members.map(m => `
            <div class="text-center p-2">
                <img class="rounded-circle mb-2" 
                     style="width: 50px; height: 50px; object-fit: cover;"
                     src="${m.image || "/web/static/img/user_placeholder.jpg"}" 
                     alt="${m.name}"/>
                <p class="small mb-0">${m.name}</p>
            </div>
        `).join("")}</div>`;
    },
});

export default publicWidget.registry.MembershipSnippet;