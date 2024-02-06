TODO:
 - [ ] Handle read-only (shared) calendars
 - [x] Handle removed calendars
 - [x] Events:

   - Attendees
   - Alarms
   - Recurrency

 - [ ] Remove deleted events
 - [x] Attachments? Yes is a requirement
 - [x] What if alarm doesn't exist?
 - [ ] Move recurrence exclusion out of this module?
 - [ ] How to check deleted events (cronjob)?
 - [x] select default calendar, in the setup wizard
 - [x] defualt in quick create?
 - [x] field with inverse for ical?
 - [ ] Delete on calendar view does not unlink
 - [ ] def change_attendee_status(self, attendee=None, \*\*kwargs):
 - [ ] nextcloud doesn't update attendee status
 - [ ] write_caldav etc not api.model
 - [ ] Fetch ordered by dtstamp asc


    # TODO: What happens here if we change from allday to non-allday (hour will be 8 because of Odoo)
    #  all exclusions will not work, this should not be fixed here as it will be problem even without the export to caldav
    #  Maybe in write function correct / adjust the exclusions field or just empty it when allday is changed?

Field like "requires export" to prevent multiple jobs being created


Use recurrence_update in def write to decide what to do...
TODO: Check changing reccency from true to false
TODO: follow_recurrence

TODO: Refactor caldav_write, caldav_create to caldav_save?
TODO: Changing non-time fields in an occurrence wont trigger a split. Is this the same in caldav?

TODO: Fix event with 4 repeats and remove the first 2 bug.
