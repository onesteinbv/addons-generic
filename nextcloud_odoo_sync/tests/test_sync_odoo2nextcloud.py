from unittest.mock import MagicMock, patch
from odoo.addons.nextcloud_odoo_sync.tests.test_sync_common import TestSyncNextcloud
from odoo.addons.nextcloud_odoo_sync.models.nextcloud_caldav import Nextcloudcaldav
from odoo.addons.nextcloud_odoo_sync.models.nc_sync_user import NcSyncUser
from caldav.objects import Calendar, Event


class TestSyncOdoo2Nextcloud(TestSyncNextcloud):
    def setUp(self):
        super().setUp()

    def mock_update_nextcloud_events(self, cal_event):
        with patch.object(
            Nextcloudcaldav,
            "get_user_calendar",
            MagicMock(spec=Nextcloudcaldav.get_user_calendar),
        ) as mock_get_user_calendar, patch.object(
            Calendar, "save_event", MagicMock(spec=Calendar.save_event)
        ) as mock_save_event, patch.object(
            Event, "save", MagicMock(spec=Calendar.save)
        ) as mock_save, patch.object(
            NcSyncUser,
            "get_nc_event_hash_by_uid",
            MagicMock(spec=NcSyncUser.get_nc_event_hash_by_uid),
        ) as mock_get_nc_event_hash_by_uid, patch.object(
            self.env.cr, "commit"
        ) as mock_cr_commit:

            mock_get_user_calendar.return_value = cal_event.parent
            mock_save_event.return_value = cal_event
            mock_save.return_value = True
            mock_get_nc_event_hash_by_uid.return_value = "test_hash"
            mock_cr_commit.return_value = True

            nextcloud_caldav_obj = self.env["nextcloud.caldav"]
            params = self.get_params()
            params2 = params.copy()

            nextcloud_caldav_obj.update_nextcloud_events(
                params["sync_user_id"], params["nc_events_dict"], **params["params"]
            )

            od_event = self.env["calendar.event"].search_read(
                [("id", "=", params2["nc_events_dict"]["create"][0]["od_event"].id)]
            )

            self.assertNextcloudEventCreated(od_event)

    def test_sync_event_create(self):
        cal_event = self.create_nextcloud_event()
        self.mock_update_nextcloud_events(cal_event)

    def test_sync_event_create_allday(self):
        cal_event = self.create_nextclound_event_allday()
        self.mock_update_nextcloud_events(cal_event)
