import {ListController} from "@web/views/list/list_controller";

export class MembershipReportListController extends ListController {
    async onClickMembershipHistoryAtDate() {
        const context = {
            active_model: this.props.resModel,
            default_only_voting_members: this.props.context.default_only_voting_members,
        };
        this.actionService.doAction({
            res_model: "membership.history.wizard",
            views: [[false, "form"]],
            target: "new",
            type: "ir.actions.act_window",
            context,
        });
    }
}
