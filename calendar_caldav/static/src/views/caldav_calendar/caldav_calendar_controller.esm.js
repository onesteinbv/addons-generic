/** @odoo-module **/

import { AttendeeCalendarController } from "@calendar/views/attendee_calendar/attendee_calendar_controller";
import { patch } from "@web/core/utils/patch";

patch(AttendeeCalendarController.prototype, "caldav_calendar_controller", {
    async onSyncCalDAVCalendarClick() {
        // Check what to do via RCP (open caldav wizard mostly)
        const action = await this.orm.call(
            "res.users",
            "action_caldav_calendar_sync",
            [[this.user.userId]],
        );
        await this.actionService.doAction(action);
    }
});
