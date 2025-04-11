/** @odoo-module */

import {MembershipReportListController} from "./membership_report_list_controller.esm";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

export const MembershipReportListView = {
  ...listView,
  Controller: MembershipReportListController,
  buttonTemplate: "MembershipReport.Buttons",
};

registry.category("views").add("membership_report_list", MembershipReportListView);
