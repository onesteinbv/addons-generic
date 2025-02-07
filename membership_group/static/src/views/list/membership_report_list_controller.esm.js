/** @odoo-module */

import {ListController} from "@web/views/list/list_controller";

export class MembershipReportListController extends ListController {
  async onClickMembershipVoteAtDate() {
    const context = {
      active_model: this.props.resModel,
    };
    this.actionService.doAction({
      res_model: "membership.vote.history",
      views: [[false, "form"]],
      target: "new",
      type: "ir.actions.act_window",
      context,
    });
  }
}
