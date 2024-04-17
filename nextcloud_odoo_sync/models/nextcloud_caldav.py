# Copyright (c) 2022 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import ast
import logging
from datetime import date as dtdate, datetime, timedelta

import pytz
import requests
from dateutil.parser import parse

from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

try:
    import caldav
    from icalendar import Alarm
except (ImportError, IOError) as err:
    _logger.debug(err)


class Nextcloudcaldav(models.AbstractModel):
    _name = "nextcloud.caldav"
    _description = "Caldav methods"

    def compare_events(self, od_events, nc_events, sync_user_id, log_obj):
        """
        This method compares the Odoo and Nextcloud events and returns
        the value to be created, modified or delete
        :param od_events: list of dictionary of Odoo events
        :param nc_events: list of dictionary of Nexcloud events
        :param sync_user_id: Recordset of the current sync user (nc.sync.user)
        :param log_obj: Recordset of the Sync Activity (nc.sync.log)
        :param return: value to be created, modified or delete
                        for odoo and nextcloud (Tuple)
        Case summary:
        Nextcloud
            - If event hash value changes from hash value recorded in
            counterpart event in Odoo, update event in Odoo
            - If event UID value does not exist in any Odoo events, add new
            event in Odoo
            - If existing UID in Odoo no longer exist in Nextcloud, delete
            event in Odoo
        Odoo
            - If nc_synced value is False, a change happen in Odoo event,
            update event in Nextcloud
            - If to_delete value is True, the event needs to be deleted in
            Nextcloud first, then delete in Odoo after sync
            - If event in Odoo has no UID and hash, create the event in
            Nextcloud (its a new event from Odoo)
        Conflict
            - If event hash value changes and Odoo event has nc_synced = False
            means both had updated the event prior to the sync
                * Need to check both event most recent modified date
                to determine which is the most recent of the two which
                will then override the other event
            - If event is recurring and UID is shared between multiple calendar
            event in Nextcloud, delete and recreate all recurring events
                * We can only delete and recreate since there is no way we can
                identify the single instance of recurring event in Nextcloud
                because they share the same UID. Some instance of a recurring
                event can have a change in date and time that is out of the
                recurrence rule scope, so we can"t rely on the recurrence rule
                to identify these events
        """
        od_events_dict = {"create": [], "write": [], "delete": []}
        nc_events_dict = {"create": [], "write": [], "delete": []}
        nc_events_create = []
        all_odoo_events = self.env["calendar.event"].search([])
        recurrence_id_key = "RECURRENCE-ID"
        # Compare Odoo events to sync
        if od_events and nc_events:
            # Odoo -> Nextcloud
            try:
                nc_event_status_confirmed_id = self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_confirmed"
                )
            except BaseException:
                raise ValidationError(
                    _(
                        "Missing value for Confirmed status."
                        "Consider upgrading the nextcloud_odoo_sync"
                        "module and try again"
                    )
                )
            for odoo_event in od_events:
                ode = odoo_event.copy()
                # Case 1: Event created in Odoo and not yet synced to Nextcloud
                # (nc_synced=False, nc_uid=False)
                od_event = ode["od_event"]
                if not ode["nc_uid"] and not od_event.nc_synced:
                    if not od_event.nc_status_id:
                        od_event.nc_status_id = nc_event_status_confirmed_id.id
                    if (
                        od_event.nc_status_id
                        and od_event.nc_status_id.name.lower() != "canceled"
                    ):
                        duplicate = self.check_duplicate(nc_events, ode)
                        if not duplicate:
                            if od_event.recurrence_id:
                                base_event = od_event.recurrence_id.base_event_id
                                if (
                                    not base_event.nc_uid
                                    and base_event not in nc_events_create
                                ):
                                    base_event_vals = {
                                        "nc_uid": base_event.nc_uid,
                                        "od_event": base_event,
                                        "event_hash": False,
                                    }
                                    if (
                                        od_event.user_id
                                        and sync_user_id.user_id == od_event.user_id
                                    ):
                                        nc_events_dict["create"].append(base_event_vals)
                                        nc_events_create.append(base_event)
                                    continue
                            else:
                                if od_event not in nc_events_create:
                                    if (
                                        od_event.user_id
                                        and sync_user_id.user_id == od_event.user_id
                                    ):
                                        nc_events_dict["create"].append(ode)
                                        nc_events_create.append(od_event)
                                    continue
                        else:
                            if (
                                od_event.user_id
                                and sync_user_id.user_id == od_event.user_id
                            ):
                                od_event.nc_uid = duplicate["nc_uid"]
                                ode["nc_uid"] = duplicate["nc_uid"]
                                duplicate["od_event"] = od_event
                                od_events_dict["write"].append(duplicate)
                            continue
                if ode["nc_uid"] and ode["event_hash"]:
                    valid_nc_uid = False
                    for nextcloud_event in nc_events:
                        if valid_nc_uid:
                            break
                        nce = nextcloud_event.copy()
                        if ode["nc_uid"] == nce["nc_uid"]:
                            valid_nc_uid = True
                            # If a matching event was found then save the
                            # caldav event in od_events_dict and save the odoo
                            # event in nc_events_dict
                            ode["nc_caldav"] = nce["nc_caldav"]
                            nce["od_event"] = od_event
                            # Case 2: If both hash values are the same
                            if ode["event_hash"] == nce["event_hash"]:
                                # Case 2.a: If Odoo event has no changes to
                                # sync (nc_synced=True) then no change to
                                # update to Nextcloud
                                if od_event.nc_synced:
                                    vevent = ode["nc_caldav"].vobject_instance.vevent
                                    if not od_event.nextcloud_calendar_type:
                                        if (
                                            "status" not in vevent.contents
                                            or vevent.status.value.lower()
                                            == "cancelled"
                                        ):
                                            if (
                                                od_event.user_id
                                                and sync_user_id.user_id
                                                == od_event.user_id
                                            ):
                                                if nce not in od_events_dict["delete"]:
                                                    od_events_dict["delete"].append(nce)
                                    if od_event.nc_to_delete:
                                        if (
                                            od_event.user_id
                                            and sync_user_id.user_id == od_event.user_id
                                        ):
                                            if ode not in nc_events_dict["delete"]:
                                                nc_events_dict["delete"].append(ode)
                                else:
                                    if not od_event.nextcloud_calendar_type:
                                        if (
                                            od_event.nc_status_id
                                            and od_event.nc_status_id.name.lower()
                                            != "canceled"
                                        ):
                                            # Case 2.b: If there are changes to
                                            # sync (nc_synced=False) and to delete
                                            # (nc_to_delete=True), delete Nextcloud
                                            # event
                                            if od_event.nc_to_delete:
                                                if (
                                                    od_event.user_id
                                                    and sync_user_id.user_id
                                                    == od_event.user_id
                                                ):
                                                    if (
                                                        ode
                                                        not in nc_events_dict["delete"]
                                                    ):
                                                        nc_events_dict["delete"].append(
                                                            ode
                                                        )
                                            # Case 2.c: If there are changes to
                                            # sync (nc_sycned=False) but not to
                                            # delete (nc_to_delete=False), update
                                            # Nextcloud event
                                            else:
                                                if (
                                                    od_event.user_id
                                                    and sync_user_id.user_id
                                                    == od_event.user_id
                                                ):
                                                    if not od_event.recurrence_id:
                                                        if (
                                                            "LAST-MODIFIED"
                                                            in nce["nc_event"][0]
                                                        ):
                                                            # The "Z" stands for Zulu time
                                                            # (zero hours ahead of GMT) which
                                                            # is another name for UTC
                                                            nc_last_modified = (
                                                                datetime.strptime(
                                                                    nce["nc_event"][0][
                                                                        "LAST-MODIFIED"
                                                                    ],
                                                                    "%Y%m%dT%H%M%SZ",
                                                                )
                                                            )
                                                            od_last_modified = (
                                                                od_event.write_date
                                                            )
                                                            if (
                                                                od_last_modified
                                                                > nc_last_modified
                                                            ):
                                                                if (
                                                                    ode
                                                                    not in nc_events_dict[
                                                                        "write"
                                                                    ]
                                                                    and not od_event.nc_synced
                                                                ):
                                                                    nc_events_dict[
                                                                        "write"
                                                                    ].append(ode)
                                                            else:
                                                                if (
                                                                    nce
                                                                    not in od_events_dict[
                                                                        "write"
                                                                    ]
                                                                ):
                                                                    if (
                                                                        od_event.nc_rid
                                                                        and "exdates"
                                                                        in nce[
                                                                            "nc_event"
                                                                        ][0]
                                                                        and od_event.nc_rid
                                                                        in nce[
                                                                            "nc_event"
                                                                        ][0]["exdates"]
                                                                    ):
                                                                        if (
                                                                            ode
                                                                            not in od_events_dict[
                                                                                "delete"
                                                                            ]
                                                                        ):
                                                                            od_events_dict[
                                                                                "delete"
                                                                            ].append(
                                                                                ode
                                                                            )
                                                                    else:
                                                                        od_events_dict[
                                                                            "write"
                                                                        ].append(nce)
                                                        else:
                                                            if (
                                                                ode
                                                                not in nc_events_dict[
                                                                    "write"
                                                                ]
                                                                and not od_event.nc_synced
                                                            ):
                                                                nc_events_dict[
                                                                    "write"
                                                                ].append(ode)
                                                        if od_event.nc_rid:
                                                            od_event_nc_rid = (
                                                                od_event.nc_rid
                                                            )
                                                            nc_modified = False
                                                            for nce_events_dict in nce[
                                                                "nc_event"
                                                            ]:
                                                                matching_values = [
                                                                    value
                                                                    for key, value in nce_events_dict.items()
                                                                    if recurrence_id_key
                                                                    in key
                                                                ]
                                                                if matching_values:
                                                                    if (
                                                                        od_event_nc_rid
                                                                        == matching_values[
                                                                            0
                                                                        ]
                                                                        and "LAST-MODIFIED"
                                                                        in nce_events_dict
                                                                    ):
                                                                        nc_last_modified = datetime.strptime(
                                                                            nce_events_dict[
                                                                                "LAST-MODIFIED"
                                                                            ],
                                                                            "%Y%m%dT%H%M%SZ",
                                                                        )
                                                                        od_last_modified = (
                                                                            od_event.write_date
                                                                        )
                                                                        if (
                                                                            od_last_modified
                                                                            > nc_last_modified
                                                                        ):
                                                                            if (
                                                                                ode
                                                                                not in nc_events_dict[
                                                                                    "write"
                                                                                ]
                                                                                and not od_event.nc_synced
                                                                            ):
                                                                                nc_events_dict[
                                                                                    "write"
                                                                                ].append(
                                                                                    ode
                                                                                )
                                                                        else:
                                                                            if (
                                                                                nce
                                                                                not in od_events_dict[
                                                                                    "write"
                                                                                ]
                                                                            ):
                                                                                recurring_nce = (
                                                                                    nce.copy()
                                                                                )
                                                                                recurring_nce.update(
                                                                                    {
                                                                                        "nc_event": [
                                                                                            nce_events_dict
                                                                                        ],
                                                                                        "detach": True,
                                                                                    }
                                                                                )
                                                                                od_events_dict[
                                                                                    "write"
                                                                                ].append(
                                                                                    recurring_nce
                                                                                )
                                                                        nc_modified = (
                                                                            True
                                                                        )
                                                                        break
                                                            if not nc_modified:
                                                                if (
                                                                    ode
                                                                    not in nc_events_dict[
                                                                        "write"
                                                                    ]
                                                                    and not od_event.nc_synced
                                                                ):
                                                                    nc_events_dict[
                                                                        "write"
                                                                    ].append(ode)
                                                    else:
                                                        if (
                                                            od_event
                                                            == od_event.recurrence_id.base_event_id
                                                        ):
                                                            if (
                                                                "LAST-MODIFIED"
                                                                in nce["nc_event"][0]
                                                            ):
                                                                # The "Z" stands for Zulu time
                                                                # (zero hours ahead of GMT) which
                                                                # is another name for UTC
                                                                nc_last_modified = datetime.strptime(
                                                                    nce["nc_event"][0][
                                                                        "LAST-MODIFIED"
                                                                    ],
                                                                    "%Y%m%dT%H%M%SZ",
                                                                )
                                                                if (
                                                                    nc_last_modified
                                                                    > od_event.recurrence_id.write_date
                                                                ):
                                                                    if (
                                                                        nce
                                                                        not in od_events_dict[
                                                                            "write"
                                                                        ]
                                                                    ):
                                                                        if (
                                                                            od_event.nc_rid
                                                                            and "exdates"
                                                                            in nce[
                                                                                "nc_event"
                                                                            ][0]
                                                                            and od_event.nc_rid
                                                                            in nce[
                                                                                "nc_event"
                                                                            ][0][
                                                                                "exdates"
                                                                            ]
                                                                        ):
                                                                            if (
                                                                                ode
                                                                                not in od_events_dict[
                                                                                    "delete"
                                                                                ]
                                                                            ):
                                                                                od_events_dict[
                                                                                    "delete"
                                                                                ].append(
                                                                                    ode
                                                                                )
                                                                        else:
                                                                            od_events_dict[
                                                                                "write"
                                                                            ].append(
                                                                                nce
                                                                            )
                                                                else:
                                                                    if (
                                                                        ode
                                                                        not in nc_events_dict[
                                                                            "write"
                                                                        ]
                                                                        and not od_event.nc_synced
                                                                    ):
                                                                        nc_events_dict[
                                                                            "write"
                                                                        ].append(ode)
                                                            else:
                                                                if (
                                                                    ode
                                                                    not in nc_events_dict[
                                                                        "write"
                                                                    ]
                                                                    and not od_event.nc_synced
                                                                ):
                                                                    nc_events_dict[
                                                                        "write"
                                                                    ].append(ode)
                                                        if od_event.nc_rid:
                                                            od_event_nc_rid = (
                                                                od_event.nc_rid
                                                            )
                                                            nc_modified = False
                                                            for nce_events_dict in nce[
                                                                "nc_event"
                                                            ]:
                                                                matching_values = [
                                                                    value
                                                                    for key, value in nce_events_dict.items()
                                                                    if recurrence_id_key
                                                                    in key
                                                                ]
                                                                if matching_values:
                                                                    if (
                                                                        od_event_nc_rid
                                                                        == matching_values[
                                                                            0
                                                                        ]
                                                                        and "LAST-MODIFIED"
                                                                        in nce_events_dict
                                                                    ):
                                                                        nc_last_modified = datetime.strptime(
                                                                            nce_events_dict[
                                                                                "LAST-MODIFIED"
                                                                            ],
                                                                            "%Y%m%dT%H%M%SZ",
                                                                        )
                                                                        nc_modified = (
                                                                            True
                                                                        )
                                                                        od_last_modified = (
                                                                            od_event.write_date
                                                                        )
                                                                        if (
                                                                            od_last_modified
                                                                            > nc_last_modified
                                                                        ):
                                                                            if (
                                                                                ode
                                                                                not in nc_events_dict[
                                                                                    "write"
                                                                                ]
                                                                                and not od_event.nc_synced
                                                                            ):
                                                                                nc_events_dict[
                                                                                    "write"
                                                                                ].append(
                                                                                    ode
                                                                                )
                                                                        else:
                                                                            if (
                                                                                nce
                                                                                not in od_events_dict[
                                                                                    "write"
                                                                                ]
                                                                            ):
                                                                                recurring_nce = (
                                                                                    nce.copy()
                                                                                )
                                                                                recurring_nce.update(
                                                                                    {
                                                                                        "nc_event": [
                                                                                            nce_events_dict
                                                                                        ],
                                                                                        "detach": True,
                                                                                    }
                                                                                )
                                                                                od_events_dict[
                                                                                    "write"
                                                                                ].append(
                                                                                    recurring_nce
                                                                                )
                                                                        break
                                                            if not nc_modified:
                                                                if (
                                                                    ode
                                                                    not in nc_events_dict[
                                                                        "write"
                                                                    ]
                                                                    and not od_event.nc_synced
                                                                ):
                                                                    nc_events_dict[
                                                                        "write"
                                                                    ].append(ode)
                                        else:
                                            if (
                                                od_event.user_id
                                                and sync_user_id.user_id
                                                == od_event.user_id
                                            ):
                                                if ode not in nc_events_dict["delete"]:
                                                    nc_events_dict["delete"].append(ode)
                                    else:
                                        if od_event.nc_to_delete:
                                            if (
                                                od_event.user_id
                                                and sync_user_id.user_id
                                                == od_event.user_id
                                            ):
                                                if ode not in nc_events_dict["delete"]:
                                                    nc_events_dict["delete"].append(ode)
                            # Case 3: If both hash differs
                            else:
                                if od_event.nextcloud_calendar_type:
                                    if od_event.nc_to_delete:
                                        if (
                                            od_event.user_id
                                            and sync_user_id.user_id == od_event.user_id
                                        ):
                                            if ode not in nc_events_dict["delete"]:
                                                nc_events_dict["delete"].append(ode)
                                    elif nce not in od_events_dict["write"]:
                                        if (
                                            od_event.user_id
                                            and sync_user_id.user_id == od_event.user_id
                                        ):
                                            od_events_dict["write"].append(nce)
                                    continue
                                # Case 3.a: If Odoo event has no change
                                # (nc_synced=True) update based on Nextcloud
                                if od_event.nc_synced:
                                    # delete if cancelled
                                    vevent = ode["nc_caldav"].vobject_instance.vevent
                                    if (
                                        "status" not in vevent.contents
                                        or vevent.status.value.lower() == "cancelled"
                                    ):
                                        if (
                                            od_event.user_id
                                            and sync_user_id.user_id == od_event.user_id
                                        ):
                                            if nce not in od_events_dict["delete"]:
                                                od_events_dict["delete"].append(nce)
                                    else:
                                        if nce not in od_events_dict["write"]:
                                            # in nextcloud an attendee can
                                            # only modify an event for itself
                                            # and will not reflect on organizer
                                            # hence we retrict modification to
                                            # odoo event by the attendee as
                                            # well
                                            if (
                                                od_event.user_id
                                                and sync_user_id.user_id
                                                == od_event.user_id
                                            ):
                                                if not od_event.recurrence_id:
                                                    if (
                                                        "LAST-MODIFIED"
                                                        in nce["nc_event"][0]
                                                    ):
                                                        # The "Z" stands for Zulu time
                                                        # (zero hours ahead of GMT) which
                                                        # is another name for UTC
                                                        nc_last_modified = (
                                                            datetime.strptime(
                                                                nce["nc_event"][0][
                                                                    "LAST-MODIFIED"
                                                                ],
                                                                "%Y%m%dT%H%M%SZ",
                                                            )
                                                        )
                                                        od_last_modified = (
                                                            od_event.write_date
                                                        )
                                                        if (
                                                            od_last_modified
                                                            > nc_last_modified
                                                        ):
                                                            if (
                                                                ode
                                                                not in nc_events_dict[
                                                                    "write"
                                                                ]
                                                                and not od_event.nc_synced
                                                            ):
                                                                nc_events_dict[
                                                                    "write"
                                                                ].append(ode)
                                                        else:
                                                            if (
                                                                nce
                                                                not in od_events_dict[
                                                                    "write"
                                                                ]
                                                            ):
                                                                if (
                                                                    od_event.nc_rid
                                                                    and "exdates"
                                                                    in nce["nc_event"][
                                                                        0
                                                                    ]
                                                                    and od_event.nc_rid
                                                                    in nce["nc_event"][
                                                                        0
                                                                    ]["exdates"]
                                                                ):
                                                                    if (
                                                                        ode
                                                                        not in od_events_dict[
                                                                            "delete"
                                                                        ]
                                                                    ):
                                                                        od_events_dict[
                                                                            "delete"
                                                                        ].append(ode)
                                                                else:
                                                                    od_events_dict[
                                                                        "write"
                                                                    ].append(nce)
                                                    else:
                                                        if (
                                                            ode
                                                            not in nc_events_dict[
                                                                "write"
                                                            ]
                                                            and not od_event.nc_synced
                                                        ):
                                                            nc_events_dict[
                                                                "write"
                                                            ].append(ode)
                                                    if od_event.nc_rid:
                                                        od_event_nc_rid = (
                                                            od_event.nc_rid
                                                        )
                                                        nc_modified = False
                                                        for nce_events_dict in nce[
                                                            "nc_event"
                                                        ]:
                                                            matching_values = [
                                                                value
                                                                for key, value in nce_events_dict.items()
                                                                if recurrence_id_key
                                                                in key
                                                            ]
                                                            if matching_values:
                                                                if (
                                                                    od_event_nc_rid
                                                                    == matching_values[
                                                                        0
                                                                    ]
                                                                    and "LAST-MODIFIED"
                                                                    in nce_events_dict
                                                                ):
                                                                    nc_last_modified = datetime.strptime(
                                                                        nce_events_dict[
                                                                            "LAST-MODIFIED"
                                                                        ],
                                                                        "%Y%m%dT%H%M%SZ",
                                                                    )
                                                                    od_last_modified = (
                                                                        od_event.write_date
                                                                    )
                                                                    if (
                                                                        od_last_modified
                                                                        > nc_last_modified
                                                                    ):
                                                                        if (
                                                                            ode
                                                                            not in nc_events_dict[
                                                                                "write"
                                                                            ]
                                                                            and not od_event.nc_synced
                                                                        ):
                                                                            nc_events_dict[
                                                                                "write"
                                                                            ].append(
                                                                                ode
                                                                            )
                                                                    else:
                                                                        if (
                                                                            nce
                                                                            not in od_events_dict[
                                                                                "write"
                                                                            ]
                                                                        ):
                                                                            recurring_nce = (
                                                                                nce.copy()
                                                                            )
                                                                            recurring_nce.update(
                                                                                {
                                                                                    "nc_event": [
                                                                                        nce_events_dict
                                                                                    ],
                                                                                    "detach": True,
                                                                                }
                                                                            )
                                                                            od_events_dict[
                                                                                "write"
                                                                            ].append(
                                                                                recurring_nce
                                                                            )
                                                                    nc_modified = True
                                                                    break
                                                        if not nc_modified:
                                                            if (
                                                                ode
                                                                not in nc_events_dict[
                                                                    "write"
                                                                ]
                                                                and not od_event.nc_synced
                                                            ):
                                                                nc_events_dict[
                                                                    "write"
                                                                ].append(ode)
                                                else:
                                                    if (
                                                        od_event
                                                        == od_event.recurrence_id.base_event_id
                                                    ):
                                                        if (
                                                            "LAST-MODIFIED"
                                                            in nce["nc_event"][0]
                                                        ):
                                                            # The "Z" stands for Zulu time
                                                            # (zero hours ahead of GMT) which
                                                            # is another name for UTC
                                                            nc_last_modified = (
                                                                datetime.strptime(
                                                                    nce["nc_event"][0][
                                                                        "LAST-MODIFIED"
                                                                    ],
                                                                    "%Y%m%dT%H%M%SZ",
                                                                )
                                                            )
                                                            if (
                                                                nc_last_modified
                                                                > od_event.recurrence_id.write_date
                                                            ):
                                                                if (
                                                                    nce
                                                                    not in od_events_dict[
                                                                        "write"
                                                                    ]
                                                                ):
                                                                    if (
                                                                        od_event.nc_rid
                                                                        and "exdates"
                                                                        in nce[
                                                                            "nc_event"
                                                                        ][0]
                                                                        and od_event.nc_rid
                                                                        in nce[
                                                                            "nc_event"
                                                                        ][0]["exdates"]
                                                                    ):
                                                                        if (
                                                                            ode
                                                                            not in od_events_dict[
                                                                                "delete"
                                                                            ]
                                                                        ):
                                                                            od_events_dict[
                                                                                "delete"
                                                                            ].append(
                                                                                ode
                                                                            )
                                                                    else:
                                                                        od_events_dict[
                                                                            "write"
                                                                        ].append(nce)
                                                            else:
                                                                if (
                                                                    ode
                                                                    not in nc_events_dict[
                                                                        "write"
                                                                    ]
                                                                    and not od_event.nc_synced
                                                                ):
                                                                    nc_events_dict[
                                                                        "write"
                                                                    ].append(ode)
                                                        else:
                                                            if (
                                                                ode
                                                                not in nc_events_dict[
                                                                    "write"
                                                                ]
                                                                and not od_event.nc_synced
                                                            ):
                                                                nc_events_dict[
                                                                    "write"
                                                                ].append(ode)
                                                    if od_event.nc_rid:
                                                        od_event_nc_rid = (
                                                            od_event.nc_rid
                                                        )
                                                        nc_modified = False
                                                        for nce_events_dict in nce[
                                                            "nc_event"
                                                        ]:
                                                            matching_values = [
                                                                value
                                                                for key, value in nce_events_dict.items()
                                                                if recurrence_id_key
                                                                in key
                                                            ]
                                                            if matching_values:
                                                                if (
                                                                    od_event_nc_rid
                                                                    == matching_values[
                                                                        0
                                                                    ]
                                                                    and "LAST-MODIFIED"
                                                                    in nce_events_dict
                                                                ):
                                                                    nc_last_modified = datetime.strptime(
                                                                        nce_events_dict[
                                                                            "LAST-MODIFIED"
                                                                        ],
                                                                        "%Y%m%dT%H%M%SZ",
                                                                    )
                                                                    od_last_modified = (
                                                                        od_event.write_date
                                                                    )
                                                                    if (
                                                                        od_last_modified
                                                                        > nc_last_modified
                                                                    ):
                                                                        if (
                                                                            ode
                                                                            not in nc_events_dict[
                                                                                "write"
                                                                            ]
                                                                            and not od_event.nc_synced
                                                                        ):
                                                                            nc_events_dict[
                                                                                "write"
                                                                            ].append(
                                                                                ode
                                                                            )
                                                                    else:
                                                                        if (
                                                                            nce
                                                                            not in od_events_dict[
                                                                                "write"
                                                                            ]
                                                                        ):
                                                                            recurring_nce = (
                                                                                nce.copy()
                                                                            )
                                                                            recurring_nce.update(
                                                                                {
                                                                                    "nc_event": [
                                                                                        nce_events_dict
                                                                                    ],
                                                                                    "detach": True,
                                                                                }
                                                                            )
                                                                            od_events_dict[
                                                                                "write"
                                                                            ].append(
                                                                                recurring_nce
                                                                            )
                                                                    nc_modified = True
                                                                    break
                                                        if not nc_modified:
                                                            if (
                                                                ode
                                                                not in nc_events_dict[
                                                                    "write"
                                                                ]
                                                                and not od_event.nc_synced
                                                            ):
                                                                nc_events_dict[
                                                                    "write"
                                                                ].append(ode)
                                            else:
                                                # revert the event of attendee
                                                # in nextcloud to event of
                                                # attendee in odoo
                                                # nc_events_dict["write"].append(
                                                #     ode)

                                                # Since is not possible to
                                                # modify the event by the
                                                # attendee in nextcloud
                                                log_obj.log_event(
                                                    message="A Nextcloud event"
                                                    " has been modified by one"
                                                    " of its attendee in Nextcloud"
                                                    " but does not get"
                                                    " reflected in the organizer"
                                                    " event. This changes will be"
                                                    " ignored in Odoo. Event details:"
                                                    "\n%s" % nce["nc_event"][0]
                                                )
                                else:
                                    # Case 3.b: If Odoo has changes
                                    # (nc_synced=False) and to delete
                                    # (nc_to_delete=True), delete Nextcloud
                                    # event
                                    if not od_event.nc_synced and od_event.nc_to_delete:
                                        if (
                                            od_event.user_id
                                            and sync_user_id.user_id == od_event.user_id
                                        ):
                                            if ode not in nc_events_dict["delete"]:
                                                nc_events_dict["delete"].append(ode)
                                    # Case 3.c: If Odoo has changes
                                    # (nc_synced=False) and not to delete
                                    # (nc_to_delete=False)
                                    else:
                                        # Check LAST-MODIFIED date value in
                                        # Nextcloud event
                                        if (
                                            od_event.user_id
                                            and sync_user_id.user_id == od_event.user_id
                                        ):
                                            if not od_event.recurrence_id:
                                                if (
                                                    "LAST-MODIFIED"
                                                    in nce["nc_event"][0]
                                                ):
                                                    # The "Z" stands for Zulu time
                                                    # (zero hours ahead of GMT) which
                                                    # is another name for UTC
                                                    nc_last_modified = (
                                                        datetime.strptime(
                                                            nce["nc_event"][0][
                                                                "LAST-MODIFIED"
                                                            ],
                                                            "%Y%m%dT%H%M%SZ",
                                                        )
                                                    )
                                                    od_last_modified = (
                                                        od_event.write_date
                                                    )
                                                    if (
                                                        od_last_modified
                                                        > nc_last_modified
                                                    ):
                                                        if (
                                                            ode
                                                            not in nc_events_dict[
                                                                "write"
                                                            ]
                                                            and not od_event.nc_synced
                                                        ):
                                                            nc_events_dict[
                                                                "write"
                                                            ].append(ode)
                                                    else:
                                                        if (
                                                            nce
                                                            not in od_events_dict[
                                                                "write"
                                                            ]
                                                        ):
                                                            if (
                                                                od_event.nc_rid
                                                                and "exdates"
                                                                in nce["nc_event"][0]
                                                                and od_event.nc_rid
                                                                in nce["nc_event"][0][
                                                                    "exdates"
                                                                ]
                                                            ):
                                                                if (
                                                                    ode
                                                                    not in od_events_dict[
                                                                        "delete"
                                                                    ]
                                                                ):
                                                                    od_events_dict[
                                                                        "delete"
                                                                    ].append(ode)
                                                            else:
                                                                od_events_dict[
                                                                    "write"
                                                                ].append(nce)
                                                else:
                                                    if (
                                                        ode
                                                        not in nc_events_dict["write"]
                                                        and not od_event.nc_synced
                                                    ):
                                                        nc_events_dict["write"].append(
                                                            ode
                                                        )
                                                if od_event.nc_rid:
                                                    od_event_nc_rid = od_event.nc_rid
                                                    nc_modified = False
                                                    for nce_events_dict in nce[
                                                        "nc_event"
                                                    ]:
                                                        matching_values = [
                                                            value
                                                            for key, value in nce_events_dict.items()
                                                            if recurrence_id_key in key
                                                        ]
                                                        if matching_values:
                                                            if (
                                                                od_event_nc_rid
                                                                == matching_values[0]
                                                                and "LAST-MODIFIED"
                                                                in nce_events_dict
                                                            ):
                                                                nc_last_modified = datetime.strptime(
                                                                    nce_events_dict[
                                                                        "LAST-MODIFIED"
                                                                    ],
                                                                    "%Y%m%dT%H%M%SZ",
                                                                )
                                                                od_last_modified = (
                                                                    od_event.write_date
                                                                )
                                                                if (
                                                                    od_last_modified
                                                                    > nc_last_modified
                                                                ):
                                                                    if (
                                                                        ode
                                                                        not in nc_events_dict[
                                                                            "write"
                                                                        ]
                                                                        and not od_event.nc_synced
                                                                    ):
                                                                        nc_events_dict[
                                                                            "write"
                                                                        ].append(ode)
                                                                else:
                                                                    if (
                                                                        nce
                                                                        not in od_events_dict[
                                                                            "write"
                                                                        ]
                                                                    ):
                                                                        recurring_nce = (
                                                                            nce.copy()
                                                                        )
                                                                        recurring_nce.update(
                                                                            {
                                                                                "nc_event": [
                                                                                    nce_events_dict
                                                                                ],
                                                                                "detach": True,
                                                                            }
                                                                        )
                                                                        od_events_dict[
                                                                            "write"
                                                                        ].append(
                                                                            recurring_nce
                                                                        )
                                                                nc_modified = True
                                                                break
                                                    if not nc_modified:
                                                        if (
                                                            ode
                                                            not in nc_events_dict[
                                                                "write"
                                                            ]
                                                            and not od_event.nc_synced
                                                        ):
                                                            nc_events_dict[
                                                                "write"
                                                            ].append(ode)
                                            else:
                                                if (
                                                    od_event
                                                    == od_event.recurrence_id.base_event_id
                                                ):
                                                    if (
                                                        "LAST-MODIFIED"
                                                        in nce["nc_event"][0]
                                                    ):
                                                        # The "Z" stands for Zulu time
                                                        # (zero hours ahead of GMT) which
                                                        # is another name for UTC
                                                        nc_last_modified = (
                                                            datetime.strptime(
                                                                nce["nc_event"][0][
                                                                    "LAST-MODIFIED"
                                                                ],
                                                                "%Y%m%dT%H%M%SZ",
                                                            )
                                                        )
                                                        if (
                                                            nc_last_modified
                                                            > od_event.recurrence_id.write_date
                                                        ):
                                                            if (
                                                                nce
                                                                not in od_events_dict[
                                                                    "write"
                                                                ]
                                                            ):
                                                                if (
                                                                    od_event.nc_rid
                                                                    and "exdates"
                                                                    in nce["nc_event"][
                                                                        0
                                                                    ]
                                                                    and od_event.nc_rid
                                                                    in nce["nc_event"][
                                                                        0
                                                                    ]["exdates"]
                                                                ):
                                                                    if (
                                                                        ode
                                                                        not in od_events_dict[
                                                                            "delete"
                                                                        ]
                                                                    ):
                                                                        od_events_dict[
                                                                            "delete"
                                                                        ].append(ode)
                                                                else:
                                                                    od_events_dict[
                                                                        "write"
                                                                    ].append(nce)
                                                        else:
                                                            if (
                                                                ode
                                                                not in nc_events_dict[
                                                                    "write"
                                                                ]
                                                                and not od_event.nc_synced
                                                            ):
                                                                nc_events_dict[
                                                                    "write"
                                                                ].append(ode)
                                                    else:
                                                        if (
                                                            ode
                                                            not in nc_events_dict[
                                                                "write"
                                                            ]
                                                            and not od_event.nc_synced
                                                        ):
                                                            nc_events_dict[
                                                                "write"
                                                            ].append(ode)
                                                if od_event.nc_rid:
                                                    od_event_nc_rid = od_event.nc_rid
                                                    nc_modified = False
                                                    for nce_events_dict in nce[
                                                        "nc_event"
                                                    ]:
                                                        matching_values = [
                                                            value
                                                            for key, value in nce_events_dict.items()
                                                            if recurrence_id_key in key
                                                        ]
                                                        if matching_values:
                                                            if (
                                                                od_event_nc_rid
                                                                == matching_values[0]
                                                                and "LAST-MODIFIED"
                                                                in nce_events_dict
                                                            ):
                                                                nc_last_modified = datetime.strptime(
                                                                    nce_events_dict[
                                                                        "LAST-MODIFIED"
                                                                    ],
                                                                    "%Y%m%dT%H%M%SZ",
                                                                )
                                                                od_last_modified = (
                                                                    od_event.write_date
                                                                )
                                                                if (
                                                                    od_last_modified
                                                                    > nc_last_modified
                                                                ):
                                                                    if (
                                                                        ode
                                                                        not in nc_events_dict[
                                                                            "write"
                                                                        ]
                                                                        and not od_event.nc_synced
                                                                    ):
                                                                        nc_events_dict[
                                                                            "write"
                                                                        ].append(ode)
                                                                else:
                                                                    if (
                                                                        nce
                                                                        not in od_events_dict[
                                                                            "write"
                                                                        ]
                                                                    ):
                                                                        recurring_nce = (
                                                                            nce.copy()
                                                                        )
                                                                        recurring_nce.update(
                                                                            {
                                                                                "nc_event": [
                                                                                    nce_events_dict
                                                                                ],
                                                                                "detach": True,
                                                                            }
                                                                        )
                                                                        od_events_dict[
                                                                            "write"
                                                                        ].append(
                                                                            recurring_nce
                                                                        )
                                                                nc_modified = True
                                                                break
                                                    if not nc_modified:
                                                        if (
                                                            ode
                                                            not in nc_events_dict[
                                                                "write"
                                                            ]
                                                            and not od_event.nc_synced
                                                        ):
                                                            nc_events_dict[
                                                                "write"
                                                            ].append(ode)
                    # Case 4: If the value of Odoo nc_uid is not found in all
                    # of Nextcloud events, then it was deleted in Nextcloud
                    if not valid_nc_uid:
                        if (
                            od_event.user_id
                            and sync_user_id.user_id == od_event.user_id
                        ):
                            if ode not in od_events_dict["delete"]:
                                od_events_dict["delete"].append(ode)
            # Nextcloud -> Odoo
            for nce in nc_events:
                vevent = nce["nc_caldav"].vobject_instance.vevent
                # ignore if cancelled
                if (
                    "status" not in vevent.contents
                    or vevent.status.value.lower() != "cancelled"
                ):
                    valid_nc_uid = all_odoo_events.filtered(
                        lambda ev: ev.nc_uid == nce["nc_uid"]
                    )
                    # for ode in od_events:
                    #     if nce["nc_uid"] == ode["nc_uid"]:
                    #         valid_nc_uid = True
                    #         break
                    # Case 5: Nextcloud nc_uid is not found in Odoo
                    if not valid_nc_uid:
                        od_events_dict["create"].append(nce)

        # Case 6: If there is not a single event in Odoo, we create everything
        # from Nextcloud -> Odoo
        if not od_events and nc_events:
            for nce in nc_events:
                vevent = nce["nc_caldav"].vobject_instance.vevent
                # ignore if cancelled
                if (
                    "status" not in vevent.contents
                    or vevent.status.value.lower() != "cancelled"
                ):
                    valid_nc_uid = all_odoo_events.filtered(
                        lambda ev: ev.nc_uid == nce["nc_uid"]
                    )
                    if not valid_nc_uid:
                        od_events_dict["create"].append(nce)
        # Case 7: If there is not a single event in Nextcloud, check if Odoo
        # event has nc_uid value or not
        if od_events and not nc_events:
            for ode in od_events:
                # ignore if cancelled
                od_event = ode["od_event"]
                if (
                    od_event.nc_status_id
                    and od_event.nc_status_id.name.lower() != "canceled"
                ):
                    # Case 7.a: If the event has an existing nc_uid value, then
                    # its a previous event in Nextcloud that might have been
                    # deleted
                    if od_event.nc_uid:
                        if (
                            od_event.user_id
                            and sync_user_id.user_id == od_event.user_id
                        ):
                            od_events_dict["delete"].append(ode)
                    else:
                        # Case 7.b: If the event has no nc_uid value then its a
                        # new event in Odoo to be created in Nextcloud
                        if (
                            od_event.user_id
                            and sync_user_id.user_id == od_event.user_id
                        ):
                            if od_event.recurrence_id:
                                base_event = od_event.recurrence_id.base_event_id
                                if (
                                    not base_event.nc_uid
                                    and base_event not in nc_events_create
                                ):
                                    base_event_vals = {
                                        "nc_uid": base_event.nc_uid,
                                        "od_event": base_event,
                                        "event_hash": False,
                                    }
                                    nc_events_dict["create"].append(base_event_vals)
                                    nc_events_create.append(base_event)
                            else:
                                if od_event not in nc_events_create:
                                    nc_events_dict["create"].append(ode)
                                    nc_events_create.append(od_event)

        return od_events_dict, nc_events_dict

    def check_duplicate(self, nc_events, ode):
        """
        Check and returns one record on a dulicated event
        :param nc_events: List of caldav nextcloud event
        :param ode: Odoo event data in a dictionary
        :return caldav nextcloud event in a dictionary
        """
        result = {}
        fields = {"name": "SUMMARY", "start": "DTSTART", "stop": "DTEND"}
        d = 0
        date_fields = ["dtstart", "dtend", "rrule", "recurrence-id", "last-modified"]
        for f in fields:
            for nce in nc_events:
                for nc_event in nce["nc_event"]:
                    for key in nc_event:
                        field = fields[f]
                        if field == key or field in key:
                            value = nc_event[key]
                            key_field = key.lower().split(";")
                            data = value
                            if key_field[0] in date_fields:
                                data = self.get_event_datetime(
                                    key_field,
                                    value,
                                    nc_event,
                                    ode["od_event"],
                                    nce["nc_caldav"],
                                )

                            allday = ode["od_event"].allday
                            if isinstance(data, datetime) or isinstance(data, dtdate):
                                if (data == ode["od_event"][f] and not allday) or (
                                    data == ode["od_event"][f].date() and allday
                                ):
                                    d += 1
                            elif data == ode["od_event"][f]:
                                d += 1
                            if d >= len(fields.keys()):
                                return nce
        return result

    def get_event_attendees(self, calendar_event, user_id, **params):
        """
        This method check if the attendee is a user of Odoo or a user of
        Nextcloud or an external contact
        :param calendar_event: caldav Event object or Odoo calendar.event recordset
        :param user_id: single recordset of res.users model
        :param **params: dictionary of keyword arguments
        :return list of res.partner model record ids
        """
        all_user_ids = params.get("all_user_ids", False)
        all_sync_user_ids = params.get("all_sync_user_ids", False)
        all_partner_ids = params.get("all_partner_ids", False)
        attendee_partner_ids = []
        nc_sync_user_obj = self.env["nc.sync.user"]
        res_partner_obj = self.env["res.partner"]
        res_users_obj = self.env["res.users"]
        org_user_id = []
        # Get attendees for Odoo event
        if isinstance(calendar_event, caldav.objects.Event):
            try:
                attendees = [
                    value.value
                    for value in calendar_event.vobject_instance.vevent.contents.get(
                        "attendee", []
                    )
                    if value
                ]
            except Exception:
                attendees = []
            try:
                organizer = calendar_event.instance.vevent.organizer.value
                attendees.append(organizer)
            except Exception:
                organizer = ""
            for att in attendees:
                email = att.split(":")[-1].lower()
                if email != "false":
                    # Check if an Odoo user has the same email address
                    att_user_id = nc_sync_user_obj.search(
                        [("nc_email", "=", email), ("sync_calendar", "=", True)],
                        limit=1,
                    ).user_id
                    if not att_user_id:
                        att_user_id = all_user_ids.filtered(
                            lambda x: x.partner_id.email
                            and x.partner_id.email.lower() == email
                        )
                    # In case more than 1 user has the same email address,
                    # check which user is in nc.sync.user model
                    if att_user_id and len(att_user_id.ids) > 1:
                        sync_user_id = all_sync_user_ids.filtered(
                            lambda x: x.user_id.id in att_user_id.ids
                        )
                        if sync_user_id:
                            attendee_partner_ids.append(
                                nc_sync_user_obj.browse(
                                    sync_user_id.ids[0]
                                ).user_id.partner_id.id
                            )
                        else:
                            attendee_partner_ids.append(
                                res_users_obj.browse(user_id.ids[0]).partner_id.id
                            )
                    else:
                        if att_user_id:
                            if not att_user_id.partner_id.email:
                                att_user_id.partner_id.email = email
                            attendee_partner_ids.append(att_user_id.partner_id.id)
                        else:
                            contact_id = res_partner_obj.search(
                                [("email", "=", email)], limit=1
                            )
                            if not contact_id:
                                contact_id = res_partner_obj.create(
                                    {"name": email, "email": email, "nc_sync": True}
                                )
                            all_partner_ids |= contact_id
                            attendee_partner_ids.append(contact_id.id)
            if organizer:
                organizer_email = organizer.replace("mailto:", "")
                org_user_id = nc_sync_user_obj.search(
                    [("nc_email", "=", organizer_email), ("sync_calendar", "=", True)],
                    limit=1,
                ).user_id
                if not org_user_id:
                    org_user_id = all_user_ids.filtered(
                        lambda x: x.partner_id.email
                        and x.partner_id.email.lower() == email
                    )
            if not attendees:
                attendee_partner_ids = [user_id.partner_id.id]
                org_user_id = user_id
        # Get attendees for Nextcloud event
        elif (
            isinstance(calendar_event, models.Model)
            and calendar_event.partner_ids
            and all_sync_user_ids
        ):
            nc_user_ids = self.env["nc.sync.user"]
            for partner in calendar_event.partner_ids:
                # In Nextcloud, we don"t populate the attendee if there is only
                # the organizer involve
                if (
                    partner != user_id.partner_id
                    and len(calendar_event.partner_ids) > 1
                ):
                    nc_user_id = all_sync_user_ids.filtered(
                        lambda x: x.partner_id.id == partner.id and x.sync_calendar
                    )
                    try:
                        nc_user_ids |= nc_user_id
                        connection_dict = nc_user_id.get_user_connection()
                        nc_user_principal = connection_dict["principal"]
                    except Exception:
                        nc_user_principal = False
                    if nc_user_id and nc_user_principal:
                        attendee_partner_ids.append(
                            nc_user_principal.get_vcal_address()
                        )
                    else:
                        # Get only partner_ids with email address
                        if partner.email:
                            attendee_partner_ids.append(f"mailto:{partner.email}")
            params["nc_user_ids"] = nc_user_ids
        return list(set(attendee_partner_ids)), org_user_id, params

    def get_event_datetime(
        self, nc_field, nc_value, vals, od_event=False, nc_event=False
    ):
        """
        This method will parse the Nextcloud event date,
        convert it to datetime in UTC timezone
        :param: nc_field: Nextcloud ical data field name
        :param: nc_value: Nextcloud ical data field value
        :param: vals: Dictionary of event values
        :param: od_event: single recordset of calendar.event model
        :return: date, datetime or string
        """
        try:
            recurrence = [x for x in list(vals) if "RECURRENCE-ID" in x]
            for key in ["LAST-MODIFIED", "DTSTART", "DTEND", "CREATED", "EXDATE"]:
                if recurrence and key in ["DTSTART", "DTEND"]:
                    # Cannot get the calendar event for single recurring instance
                    # hence we revent to string manipulation of date
                    event_date = nc_event.icalendar_component.get(key).dt
                    tz = "UTC"
                    if isinstance(event_date, datetime):
                        tz = event_date.tzinfo.zone
                    date = parse(nc_value)
                    if (
                        od_event
                        and od_event.nextcloud_event_timezone
                        and od_event.nextcloud_event_timezone == tz
                    ):
                        dt_tz = pytz.timezone(tz).localize(date, is_dst=None)
                        date = dt_tz.astimezone(pytz.utc)
                    else:
                        if tz != "UTC":
                            date = date.astimezone(pytz.utc)
                    value = nc_field[-1].split("=")[-1]
                    if value == "date":
                        if nc_field[0].upper() == "DTEND":
                            date = date - timedelta(days=1)
                        return date.date()
                    return date.replace(tzinfo=None)
                elif key in nc_field[0].upper():
                    if "EXDATE" in key:
                        exdate_val = nc_event.icalendar_component.get(key)
                        date = (
                            [exdate_val]
                            if not isinstance(exdate_val, list)
                            else exdate_val
                        )
                    else:
                        date = nc_event.icalendar_component.get(key).dt
                    if isinstance(date, datetime):
                        tz = date.tzinfo.zone
                        if tz != "UTC":
                            date = date.astimezone(pytz.utc)
                    elif isinstance(date, list):
                        data = []
                        all_day = False
                        if od_event and od_event.allday:
                            all_day = True
                        for exdate in date:
                            for item in exdate.dts:
                                date_data = item.dt
                                tz = date_data.tzinfo.zone
                                if tz != "UTC":
                                    date_data = date_data.astimezone(pytz.utc)
                                if all_day and isinstance(date_data, datetime):
                                    date_data = date_data.date()
                                data.append(date_data.replace(tzinfo=None))
                        return data
                    else:
                        if key == "DTEND":
                            date = date - timedelta(days=1)
                    value = nc_field[-1].split("=")[-1]
                    if value == "date" and isinstance(date, datetime):
                        date = date.date()
                    if isinstance(date, datetime):
                        return date.replace(tzinfo=None)
                    else:
                        return date
            return nc_value
        except Exception:
            return nc_value

    def get_recurrence_id_date(self, nc_field, nc_value, od_event_id):
        """
        This method will parse the recurrence ID, convert to UTC
        :param: nc_field: Nextcloud ical data field name
        :param: nc_value: Nextcloud ical data field value
        :param: od_event_id: single recordset of calendar.event model
        :return: date or datetime
        """
        tz = nc_field[-1].split("=")[-1]
        if "Z" in nc_value:
            nc_value = nc_value.replace("Z", "")
        date_value = parse(nc_value)
        if od_event_id and od_event_id.allday and isinstance(date_value, datetime):
            return date_value.date()
        # else:
        #     data = self.convert_date(date_value, tz, "utc")

        return date_value

    def manage_recurring_instance(self, event_dict, operation, vals):
        """
        This method manages the changes for a single instance
        of a recurring event
        :param event_dict: dictionary, Odoo and Nextcloud events
        :param operation: string, indicate create, write or delete operation
        :param vals: Dictionary of event values
        :return single recordset of calendar.event model,
                string, dictionary of values
        """
        exdates = []
        vevent = False
        caldav_event = event_dict.get("nc_caldav", False)
        if caldav_event:
            vevent = caldav_event.vobject_instance.vevent
        event_id = event_dict.get("od_event", False)
        date_format = "%Y%m%dT%H%M%S"
        if event_id.allday:
            date_format = "%Y%m%d"
        if caldav_event:
            prev_exdates = vevent.contents.pop("exdate", False)
            if prev_exdates:
                exdates = prev_exdates[0].value
                for index, item in enumerate(exdates):
                    if not isinstance(item, datetime):
                        exdates[index] = datetime.combine(item, datetime.min.time())
        if event_id.recurrence_id.nc_exdate:
            od_exdates = [
                parse(x) for x in ast.literal_eval(event_id.recurrence_id.nc_exdate)
            ]
            [exdates.append(d) for d in od_exdates if d not in exdates]
        # Handle create and delete operation
        recurring_event_ids = event_id.recurrence_id.calendar_event_ids
        if exdates and operation == "create":
            # Check for detached events in Odoo
            detach_ids = recurring_event_ids.filtered(
                lambda x: x.nc_detach and x.nc_rid
            )
            if detach_ids:
                detach_exdates = [parse(x.nc_rid) for x in detach_ids]
                [exdates.append(d) for d in detach_exdates if d not in exdates]
            vals["exdate"] = exdates
        if operation == "delete":
            # Check if all instance of recurring events are for deletion
            to_delete_ids = recurring_event_ids.filtered(
                lambda x: x.nc_to_delete and x.nc_rid
            )
            if not to_delete_ids or len(to_delete_ids.ids) == len(
                event_id.recurrence_id.calendar_event_ids.ids
            ):
                return event_id, operation, vals
            else:
                exdates.extend(
                    [parse(x.nc_rid) for x in to_delete_ids if x.nc_rid not in exdates]
                )

        # Handle write operation by marking the existing caldav_event with exdate
        # then create a new caldav_event that is detached from recurring rule
        if operation == "write" and event_id.nc_detach:
            [vals.pop(x, False) for x in ["rrule", "uid", "exdate"] if x in vals]
            exdate = parse(event_id.nc_rid) if event_id.nc_rid else False
            if exdate and exdate not in exdates:
                exdates.append(exdate)
            event_id.recurrence_id.nc_exdate = [
                x.strftime(date_format) for x in exdates
            ]
            operation = "create"
        if (
            operation == "write"
            and not event_id.nc_detach
            and event_id.recurrence_id.base_event_id == event_id
        ):
            operation = "create"
        # Set the exdates value in the caldav_event
        if exdates and caldav_event:
            for index, value in enumerate(exdates):
                if isinstance(value, datetime):
                    if not value.tzinfo:
                        dt_tz = pytz.timezone(
                            event_id.nextcloud_event_timezone
                            or event_id.event_tz
                            or "UTC"
                        ).localize(value, is_dst=None)
                    else:
                        dt_tz = value
                    exdates[index] = dt_tz.date() if event_id.allday else dt_tz
            exdates = list(set(exdates))
            parameters = {"VALUE": "DATE" if event_id.allday else "DATE-TIME"}
            if not event_id.allday:
                parameters.update(
                    {
                        "TZID": event_id.nextcloud_event_timezone
                        or event_id.event_tz
                        or "UTC"
                    }
                )
            caldav_event.icalendar_component.add(
                "exdate", exdates, parameters=parameters
            )
            caldav_event.save()
        return event_id, operation, vals

    def get_rrule_dict(self, rrule):
        """
        This method converts the rrule string into a dictionary of values
        :param rrule: Recurring rule (string)
        :return rrule dictionary
        """
        rrule = rrule.split(":")[-1]
        result = {}
        for rec in rrule.split(";"):
            k, v = rec.split("=")
            try:
                v = int(v)
            except BaseException:
                pass
            result.update({k: v})
        return result

    def update_event_hash(self, hash_vals, event_ids=False):
        """
        This method updates the hash value of the event
        :param hash_vals: dict, dictionary of sync user and event hash values
        :param event_ids: single/multiple recordset of calendar.event model
        """
        # Update the hash value of the Odoo event that corresponds to the
        # current user_id
        calendar_event_nc_hash_obj = self.env["calendar.event.nchash"]
        if event_ids:
            event_ids.nc_synced = True
            for event in event_ids:
                hash_id = event.nc_hash_ids.filtered(
                    lambda x: x.nc_sync_user_id.id == hash_vals["nc_sync_user_id"]
                )
                if hash_id:
                    hash_id.nc_event_hash = hash_vals["nc_event_hash"]
                else:
                    # Create the hash value for the event if not exist
                    hash_vals["calendar_event_id"] = event.id
                    calendar_event_nc_hash_obj.create(hash_vals)

        elif not event_ids and "principal" in hash_vals:
            events_hash = hash_vals["events"]
            principal = hash_vals["principal"]
            sync_user_id = self.env["nc.sync.user"].browse(hash_vals["nc_sync_user_id"])
            calendars = principal.calendars()
            all_user_events = []
            for calendar in calendars:
                if (
                    calendar.canonical_url
                    not in sync_user_id.nc_calendar_ids.mapped("calendar_url")
                    and not calendar.canonical_url
                    == sync_user_id.nc_calendar_id.calendar_url
                ):
                    continue
                start_date = datetime.combine(
                    sync_user_id.start_date or dtdate.today(), datetime.min.time()
                )
                events = calendar.search(
                    start=start_date,
                    event=True,
                )
                if events:
                    all_user_events.extend(events)
            for event in all_user_events:
                nc_uid = event.vobject_instance.vevent.uid.value
                if nc_uid in events_hash:
                    event_vals = sync_user_id.get_event_data(event)
                    new_vals = {
                        "nc_sync_user_id": sync_user_id.id,
                        "nc_event_hash": event_vals["hash"],
                    }
                    event_id = events_hash[nc_uid]
                    if event_id.recurrence_id:
                        event_id = event_id.recurrence_id.calendar_event_ids
                        event_id.nc_uid = nc_uid
                    self.update_event_hash(new_vals, event_id)

    def update_attendee_invite(self, event_ids):
        """
        This method accepts the invitation for the meeting organizer
        as part of attendee which is Odoo default behavior
        :param event_ids: single/multiple recordset of calendar.event model
        """
        for event in event_ids:
            attendee_id = event.attendee_ids.filtered(
                lambda x: x.partner_id == event.user_id.partner_id
            )
            if attendee_id:
                attendee_id.state = "accepted"

    def delete_exempted_event(self, event_id, exdates, all_odoo_event_ids):
        """
        This method deletes an instance of a recurring event that was
        already deleted in Nextcloud
        :param event_id: single recordset of calendar.event model
        :param exdates: dictionary of event UID and EXDATE value from Nextcloud
        :param all_odoo_event_ids: multiple recordset of calendar.event model
        :return recordset: returns a new list of all_odoo_event_ids
                            where delete events were removed
        """
        if exdates and event_id.nc_uid in exdates and event_id.recurrence_id:
            recurring_event_ids = event_id.recurrence_id.calendar_event_ids
            ex_recurring_event_ids = recurring_event_ids.filtered(
                lambda x: x.nc_rid in exdates[event_id.nc_uid]
            )
            if ex_recurring_event_ids:
                all_odoo_event_ids = all_odoo_event_ids.filtered(
                    lambda x: x not in ex_recurring_event_ids
                )
                ex_recurring_event_ids.sudo().with_context(force_delete=True).unlink()
        return all_odoo_event_ids

    def update_odoo_events(self, sync_user_id, od_events_dict, **params):
        """
        This method updates the Odoo calendar.event records from Caldav events
        :param sync_user_id: single recordset of nc.sync.user model
        :param od_events_dict: dictionary of create, write and
                delete operations for Odoo
        :param **params: dictionary of keyword arguments containing multiple
                recordset of models
        """
        all_odoo_event_ids = params.get("all_odoo_event_ids", False)
        all_nc_calendar_ids = params.get("all_nc_calendar_ids", False)
        all_odoo_event_type_ids = params.get("all_odoo_event_type_ids", False)
        status_vals = params.get("status_vals", False)
        calendar_event = self.env["calendar.event"].sudo()
        calendar_recurrence_obj = self.env["calendar.recurrence"].sudo()
        field_mapping = self.get_caldav_fields()
        date_fields = ["dtstart", "dtend", "rrule", "recurrence-id", "last-modified"]
        log_obj = params["log_obj"]
        user_id = sync_user_id.user_id
        user_name = sync_user_id.user_id.name
        nc_event_status_confirmed_id = self.env.ref(
            "nextcloud_odoo_sync.nc_event_status_confirmed"
        )
        for operation in od_events_dict:
            for event in od_events_dict[operation]:
                od_event_id = event["od_event"] if "od_event" in event else False
                new_event_id = False
                detach = event.get("detach", False)
                if od_event_id and not od_event_id.exists():
                    continue
                    # Perform delete operation
                try:
                    if (
                        operation == "delete"
                        and "od_event" in event
                        and event["od_event"]
                    ):
                        all_odoo_event_ids = all_odoo_event_ids - event["od_event"]
                        event["od_event"].sudo().with_context(
                            force_delete=True
                        ).unlink()
                        params["delete_count"] += len(event["od_event"])
                except Exception as e:
                    message = "Error deleting Odoo event '%s' for user '%s':\n" % (
                        event["od_event"],
                        user_name,
                    )
                    log_obj.log_event(
                        mode="error",
                        error=e,
                        message=message,
                        operation_type="delete",
                    )
                    params["error_count"] += 1
                    continue
                nc_event = event["nc_event"] if "nc_event" in event else False
                caldav_event = event["nc_caldav"] if "nc_caldav" in event else False
                event_hash = event["event_hash"]
                exdates = {}
                if nc_event:
                    for vevent in nc_event:
                        if od_event_id and not od_event_id.exists():
                            continue
                        if operation == "create" and new_event_id:
                            od_event_id = new_event_id
                        vals = {"nc_uid": event["nc_uid"]}
                        nc_uid = event["nc_uid"]
                        all_day = False
                        # Loop through each fields from the Nextcloud event and
                        # map it to Odoo fields
                        for e in vevent:
                            field = e.lower().split(";")
                            if field[0] in field_mapping or field[0] == "exdates":
                                data = vevent[e]
                                if field[0] in date_fields:
                                    data = self.get_event_datetime(
                                        field,
                                        vevent[e],
                                        vevent,
                                        od_event_id,
                                        caldav_event,
                                    )
                                if field[0] == "dtstart" and not isinstance(
                                    data, datetime
                                ):
                                    all_day = True
                                if field[0] == "transp":
                                    if vevent[e].lower() == "opaque":
                                        data = "busy"
                                    elif vevent[e].lower() == "transparent":
                                        data = "free"
                                elif field[0] == "status" and status_vals:
                                    data = status_vals[vevent[e].lower()]
                                elif field[0] == "valarm":
                                    data = self.get_odoo_alarms(vevent.get(e, []))
                                elif field[0] == "categories":
                                    (
                                        data,
                                        params["all_odoo_event_type_ids"],
                                    ) = self.get_odoo_categories(
                                        all_odoo_event_type_ids,
                                        vevent[e],
                                    )
                                elif field[0] == "rrule":
                                    vals["recurrency"] = True
                                    vals["rrule"] = data
                                    data = False
                                elif field[0] == "exdates" and data:
                                    if nc_uid not in exdates:
                                        exdates[nc_uid] = []
                                    for item in data:
                                        if isinstance(item, datetime):
                                            item = item.strftime("%Y%m%dT%H%M%S")
                                        elif isinstance(item, dtdate):
                                            item = item.strftime("%Y%m%d")
                                        exdates[nc_uid].append(item)
                                    data = False
                                elif field[0] == "recurrence-id" and data:
                                    try:
                                        data = self.get_recurrence_id_date(
                                            field, vevent[e], od_event_id
                                        )
                                    except:
                                        pass
                                    # Convert it back to string for matching
                                    # with nc_rid field of calendar.event model
                                    if isinstance(data, datetime):
                                        data = data.strftime("%Y%m%dT%H%M%S")
                                    elif isinstance(data, dtdate):
                                        data = data.strftime("%Y%m%d")
                                if data:
                                    vals[field_mapping[field[0]]] = data
                        if caldav_event.icalendar_component.get("DTSTART"):
                            event_start_date = caldav_event.icalendar_component.get(
                                "DTSTART"
                            ).dt
                            tz = False
                            if isinstance(event_start_date, datetime):
                                tz = event_start_date.tzinfo.zone
                            if tz:
                                vals["nextcloud_event_timezone"] = tz
                        if caldav_event.icalendar_component.get(
                            "X-NEXTCLOUD-BC-FIELD-TYPE"
                        ):
                            vals[
                                "nextcloud_calendar_type"
                            ] = caldav_event.icalendar_component.get(
                                "X-NEXTCLOUD-BC-FIELD-TYPE"
                            )
                        if all_day:
                            vals["start_date"] = vals.pop("start")
                            vals["stop_date"] = vals.pop("stop")
                        if detach:
                            vals["recurrence_id"] = False
                            vals["recurrency"] = False
                        # Populate the nc_calendar_ids field in Odoo
                        nc_calendar_id = all_nc_calendar_ids.filtered(
                            lambda x: x.calendar_url
                            == caldav_event.parent.canonical_url
                            and x.user_id == user_id
                        )
                        if all_odoo_event_ids:
                            event_nc_calendar_ids = all_odoo_event_ids.filtered(
                                lambda x: x.nc_uid == vals["nc_uid"]
                            ).mapped("nc_calendar_ids")
                            user_nc_calendar_ids = all_nc_calendar_ids.filtered(
                                lambda x: x.user_id == user_id
                            )
                            new_nc_calendar_ids = list(
                                set(event_nc_calendar_ids.ids)
                                - set(user_nc_calendar_ids.ids)
                            )
                        else:
                            new_nc_calendar_ids = []
                        if nc_calendar_id:
                            new_nc_calendar_ids.append(nc_calendar_id.id)
                        if vals.get("rrule", False):
                            vals["nextcloud_rrule"] = vals.get("rrule")
                        # clear categ_ids when not present
                        if "categ_ids" not in vals:
                            vals["categ_ids"] = [(6, 0, [])]
                        # clear alarm_ids when not present
                        if "alarm_ids" not in vals:
                            vals["alarm_ids"] = [(6, 0, [])]
                        # Set the status
                        if "nc_status_id" not in vals:
                            vals["nc_status_id"] = nc_event_status_confirmed_id.id
                        # Populate attendees and rest of remaining fields
                        event_name = vals.get("name", "Untitled event")
                        vals.pop("write_date", False)
                        (
                            attendee_partner_ids,
                            organizer,
                            params,
                        ) = self.get_event_attendees(caldav_event, user_id, **params)
                        organizer_user_id = organizer[0].id if organizer else False
                        hash_vals_list = [
                            {
                                "nc_sync_user_id": sync_user_id.id,
                                "nc_event_hash": event_hash,
                            }
                        ]
                        if organizer_user_id:
                            nc_sync_user_id = self.env["nc.sync.user"].search(
                                [
                                    ("user_id", "=", organizer_user_id),
                                    ("sync_calendar", "=", True),
                                ],
                                limit=1,
                            )
                            if nc_sync_user_id != sync_user_id:
                                (
                                    nc_user_event_hash,
                                    nc_sync_user_calendar_id,
                                ) = nc_sync_user_id.get_nc_event_hash_by_uid_for_other_user(
                                    nc_uid
                                )
                                hash_vals_list.append(
                                    {
                                        "nc_sync_user_id": nc_sync_user_id.id,
                                        "nc_event_hash": nc_user_event_hash,
                                    }
                                )
                                if nc_sync_user_calendar_id:
                                    new_nc_calendar_ids.append(
                                        nc_sync_user_calendar_id.id
                                    )
                        vals["nc_calendar_ids"] = [(6, 0, new_nc_calendar_ids)]
                        vals.update(
                            {
                                "partner_ids": [(6, 0, attendee_partner_ids)],
                                "allday": all_day,
                                "nc_allday": all_day,
                                "nc_synced": True,
                                "user_id": organizer_user_id,
                            }
                        )
                        # Perform create operation
                        if operation == "create":
                            try:
                                new_event_id = False
                                # Check if the event is part of recurring event
                                if "nc_rid" in vals and nc_uid:
                                    recurring_event_id = all_odoo_event_ids.filtered(
                                        lambda x: x.nc_uid == nc_uid
                                        and x.nc_rid == vals["nc_rid"]
                                    )
                                    if recurring_event_id:
                                        recurring_event_id.with_context(
                                            sync_from_nextcloud=True
                                        ).write(vals)
                                        self.update_attendee_invite(recurring_event_id)
                                        for hash_vals in hash_vals_list:
                                            self.update_event_hash(
                                                hash_vals, recurring_event_id
                                            )
                                        all_odoo_event_ids = self.delete_exempted_event(
                                            recurring_event_id,
                                            exdates,
                                            all_odoo_event_ids,
                                        )
                                else:
                                    nc_hash_ids = []
                                    for hash_vals in hash_vals_list:
                                        nc_hash_ids.append((0, 0, hash_vals))
                                    vals["nc_hash_ids"] = nc_hash_ids
                                    context_dict = {"sync_from_nextcloud": True}
                                    if caldav_event.icalendar_component.get(
                                        "RELATED-TO"
                                    ):
                                        if (
                                            "until"
                                            in vals.get("nextcloud_rrule", "").lower()
                                        ):
                                            context_dict.update({"update_until": True})
                                    new_event_id = calendar_event.with_context(
                                        context_dict
                                    ).create(vals)
                                    if (
                                        new_event_id.recurrence_id
                                        and new_event_id.recurrence_id.calendar_event_ids
                                    ):
                                        recurring_event_ids = (
                                            new_event_id.recurrence_id.calendar_event_ids
                                        )
                                        all_odoo_event_ids |= recurring_event_ids
                                        self.update_attendee_invite(recurring_event_ids)
                                        for hash_vals in hash_vals_list:
                                            self.update_event_hash(
                                                hash_vals, recurring_event_ids
                                            )
                                        all_odoo_event_ids = self.delete_exempted_event(
                                            new_event_id, exdates, all_odoo_event_ids
                                        )

                                    else:
                                        all_odoo_event_ids |= new_event_id
                                # In Odoo, the organizer is by default part of
                                # the attendee and automatically accepts the invite
                                # Accepted calendar event in Odoo appears with
                                # background filled in Calendar view
                                if new_event_id:
                                    self.update_attendee_invite(new_event_id)
                                # Commit the changes to the database
                                self.env.cr.commit()
                                params["create_count"] += 1
                            except Exception as e:
                                message = (
                                    "Error creating Odoo event '%s' for user '%s':\n"
                                    % (event_name, user_name)
                                )
                                log_obj.log_event(
                                    mode="error",
                                    error=e,
                                    message="Error creating Odoo event",
                                    operation_type="create",
                                )
                                params["error_count"] += 1
                            continue
                        # Perform write operation
                        if operation == "write" and od_event_id:
                            try:
                                # We don"t update if the event only contains
                                # rrule but no nc_rid
                                if "rrule" in vals and "nc_rid" not in vals:
                                    if od_event_id.exists():
                                        if (
                                            od_event_id.recurrence_id.base_event_id
                                            == od_event_id
                                        ):
                                            update = self.check_recurrent_event_vals(
                                                od_event_id, vals
                                            )
                                            if update:
                                                recurrence_vals = vals
                                                (
                                                    od_event_id.recurrence_id.calendar_event_ids
                                                    - od_event_id.recurrence_id.base_event_id
                                                ).write({"nc_uid": False})
                                                recurrence_vals.update(
                                                    {"recurrence_update": "all_events"}
                                                )
                                                recurring_events = (
                                                    od_event_id.recurrence_id.calendar_event_ids
                                                )
                                                context_dict = {
                                                    "sync_from_nextcloud": True
                                                }
                                                if (
                                                    (
                                                        vals.get(
                                                            "nextcloud_rrule", False
                                                        )
                                                        and od_event_id.nextcloud_rrule
                                                        != vals.get("nextcloud_rrule")
                                                    )
                                                    or (
                                                        od_event_id.allday
                                                        and (
                                                            (
                                                                vals.get(
                                                                    "start_date", False
                                                                )
                                                                and vals.get(
                                                                    "start_date"
                                                                )
                                                                == od_event_id.start_date
                                                            )
                                                            or (
                                                                vals.get(
                                                                    "stop_date", False
                                                                )
                                                                and vals.get(
                                                                    "stop_date"
                                                                )
                                                                == od_event_id.stop_date
                                                            )
                                                        )
                                                    )
                                                    or (
                                                        not od_event_id.allday
                                                        and (
                                                            (
                                                                vals.get("start", False)
                                                                and vals.get("start")
                                                                == od_event_id.start
                                                            )
                                                            or (
                                                                vals.get("stop", False)
                                                                and vals.get("stop")
                                                                == od_event_id.stop
                                                            )
                                                        )
                                                    )
                                                ):
                                                    recurrence_vals.update(
                                                        {
                                                            "nextcloud_rrule": vals[
                                                                "nextcloud_rrule"
                                                            ]
                                                        }
                                                    )
                                                    recurrence_vals.update(
                                                        {
                                                            "rrule": vals[
                                                                "nextcloud_rrule"
                                                            ]
                                                        }
                                                    )
                                                    recurrence_vals.update(
                                                        calendar_recurrence_obj._rrule_parse(
                                                            vals["nextcloud_rrule"],
                                                            vals.get(
                                                                "start",
                                                                od_event_id.start,
                                                            ),
                                                        )
                                                    )
                                                    if (
                                                        vals.get(
                                                            "nextcloud_rrule", False
                                                        )
                                                        and od_event_id.nextcloud_rrule
                                                        != vals.get("nextcloud_rrule")
                                                    ) and "until" in vals[
                                                        "nextcloud_rrule"
                                                    ].lower():
                                                        context_dict.update(
                                                            {"update_until": True}
                                                        )
                                                    context_dict.update(
                                                        {"update_nc_rid": True}
                                                    )
                                                else:
                                                    recurrence_vals.pop("rrule", None)
                                                    recurrence_vals.pop(
                                                        "nextcloud_rrule", None
                                                    )
                                                od_event_id.recurrence_id.base_event_id.with_context(
                                                    context_dict
                                                ).write(
                                                    recurrence_vals
                                                )
                                                new_recurring_events = (
                                                    od_event_id.recurrence_id.calendar_event_ids
                                                )
                                                if not od_event_id.active:
                                                    new_recurrence = (
                                                        calendar_recurrence_obj.search(
                                                            [
                                                                (
                                                                    "base_event_id",
                                                                    "=",
                                                                    od_event_id.id,
                                                                )
                                                            ],
                                                            limit=1,
                                                        )
                                                    )
                                                    if new_recurrence:
                                                        new_recurring_events = new_recurrence.calendar_event_ids.sorted(
                                                            key=lambda r: r.start
                                                        )
                                                        if new_recurring_events:
                                                            all_odoo_event_ids = (
                                                                all_odoo_event_ids
                                                                - od_event_id
                                                            )
                                                            recurring_events = (
                                                                recurring_events
                                                                - od_event_id
                                                            )
                                                            od_event_id.with_context(
                                                                force_delete=True
                                                            ).unlink()
                                                            new_recurrence.base_event_id = new_recurring_events[
                                                                0
                                                            ].id
                                                            od_event_id = (
                                                                new_recurring_events[0]
                                                            )
                                                all_odoo_event_ids = self.update_recurring_events_in_all_events(
                                                    new_recurring_events,
                                                    recurring_events,
                                                    all_odoo_event_ids,
                                                )
                                                if context_dict.get("update_nc_rid"):
                                                    if not od_event_id.allday:
                                                        start = od_event_id.start
                                                        tz = (
                                                            od_event_id.nextcloud_event_timezone
                                                        )
                                                        if tz:
                                                            dt_tz = start.replace(
                                                                tzinfo=pytz.utc
                                                            )
                                                            start = dt_tz.astimezone(
                                                                pytz.timezone(tz)
                                                            )
                                                            od_event_id.nc_rid = (
                                                                start.strftime(
                                                                    "%Y%m%dT%H%M%S"
                                                                )
                                                            )
                                                        else:
                                                            od_event_id.nc_rid = (
                                                                od_event_id.nc_rid
                                                            )
                                                    else:
                                                        od_event_id.nc_rid = (
                                                            od_event_id.start.strftime(
                                                                "%Y%m%d"
                                                            )
                                                        )
                                                for hash_vals in hash_vals_list:
                                                    self.update_event_hash(
                                                        hash_vals, new_recurring_events
                                                    )
                                        for hash_vals in hash_vals_list:
                                            self.update_event_hash(
                                                hash_vals, od_event_id
                                            )
                                    all_odoo_event_ids = self.delete_exempted_event(
                                        od_event_id, exdates, all_odoo_event_ids
                                    )
                                    self.env.cr.commit()
                                    params["write_count"] += 1
                                    continue
                                # Check if the event is part of recurring event
                                elif (
                                    "rrule" not in vals
                                    and "nc_rid" in vals
                                    and od_event_id
                                    and od_event_id.recurrence_id
                                ):
                                    recurring_event_ids = (
                                        od_event_id.recurrence_id.calendar_event_ids
                                    )
                                    recurring_event_id = recurring_event_ids.filtered(
                                        lambda x: x.nc_rid == vals["nc_rid"]
                                    )
                                    if not recurring_event_id:
                                        continue
                                    else:
                                        od_event_id = recurring_event_id
                                vals.pop("nextcloud_event_timezone", None)
                                od_event_id.with_context(
                                    sync_from_nextcloud=True
                                ).write(vals)
                                # # Update the hash value of the Odoo event that
                                # # corresponds to the current user_id
                                # if od_event_id.recurrence_id:
                                #     od_event_id = (
                                #         od_event_id.recurrence_id.calendar_event_ids
                                #     )
                                # Update hash values and attendee invite
                                self.update_attendee_invite(od_event_id)
                                for hash_vals in hash_vals_list:
                                    self.update_event_hash(hash_vals, od_event_id)
                                all_odoo_event_ids = self.delete_exempted_event(
                                    od_event_id, exdates, all_odoo_event_ids
                                )
                                # Commit the changes to the database
                                self.env.cr.commit()
                                params["write_count"] += 1
                            except Exception as e:
                                message = (
                                    "Error updating Odoo event '%s' for user '%s':\n"
                                    % (event_name, user_name)
                                )
                                log_obj.log_event(
                                    mode="error",
                                    error=e,
                                    message=message,
                                    operation_type="write",
                                )
                                params["error_count"] += 1
        params["all_odoo_event_ids"] = all_odoo_event_ids
        return params

    def update_nextcloud_events(self, sync_user_id, nc_events_dict, **params):
        """
        This method updates the Nexcloud calendar event records from Odoo
        :param sync_user_id: single recordset of nc.sync.user model
        :param nc_events_dict: dictionary of create, write and delete
                operations for Nextcloud
        :param **params: dictionary of keyword arguments containing
                multiple recordset of models
        """
        calendar_event_obj = self.env["calendar.event"]
        connection = params.get("connection", False)
        principal = params.get("principal", False)
        fields = calendar_event_obj._fields
        update_events_hash = {}
        # Reverse the mapping of the field in get_caldav_fiels() method for
        # Odoo -> Nextcloud direction
        field_mapping = {v: k for k, v in self.get_caldav_fields().items()}
        alarms_mapping = {v: k for k, v in self.get_alarms_mapping().items()}
        log_obj = params["log_obj"]
        user_name = sync_user_id.user_id.name
        recurrent_rule_ids = {}
        for operation in nc_events_dict:
            recurrent_rule_ids[operation] = []
            prev_operation = operation
            for event in nc_events_dict[operation]:
                current_operation = operation
                event_id = event["od_event"]
                if event_id and not event_id.exists():
                    continue
                caldav_event = event.get("nc_caldav", False)
                vevent = False
                if caldav_event:
                    vevent = caldav_event.vobject_instance.vevent
                if event_id.recurrence_id:
                    if (
                        event_id.recurrence_id in recurrent_rule_ids[operation]
                        and not event_id.nc_detach
                    ):
                        continue
                    else:
                        if operation == "create" and not event_id.nc_detach:
                            # Get the first event of the recurring event by
                            # sorting it by record id
                            event_ids = (
                                event_id.recurrence_id.calendar_event_ids.sorted(
                                    key=lambda r: r.start
                                )
                            )
                            event_id = calendar_event_obj.browse(event_ids.ids[0])
                attendees = []
                vals = {}
                # Loop through each fields from the Nextcloud event and map it
                # to Odoo fields with values
                for field in field_mapping:
                    if (
                        field not in fields
                        or not event_id[field]
                        or field in ["id", "write_date", "nc_rid"]
                    ):
                        continue
                    value = event_id[field]
                    if field in ["start", "stop"]:
                        if "allday" in event_id and event_id["allday"]:
                            start_stop = {
                                "start": event_id["start_date"],
                                "stop": event_id["stop_date"] + timedelta(days=1),
                            }
                            vals[field_mapping[field]] = start_stop[field]
                        else:
                            user_tz = (
                                event_id.nextcloud_event_timezone
                                or sync_user_id.user_id.tz
                            )
                            vals[field_mapping[field]] = self.convert_date(
                                value, user_tz, "local"
                            )
                    elif field == "partner_ids":
                        attendees, organizer, params = self.get_event_attendees(
                            event_id, sync_user_id.user_id, **params
                        )
                    elif field == "description":
                        description = html2plaintext(value)
                        if description != "" or description:
                            vals[field_mapping[field]] = description
                    elif field == "show_as":
                        show_as = {"free": "TRANSPARENT", "busy": "OPAQUE"}
                        vals[field_mapping[field]] = show_as[value]
                    elif field == "nc_status_id":
                        vals[field_mapping[field]] = value.name.upper()
                    elif field == "alarm_ids":
                        vals[field_mapping[field]] = [
                            alarms_mapping.get(x.id)
                            for x in value
                            if x.id in alarms_mapping.keys()
                        ]
                        if not vals[field_mapping[field]]:
                            vals.pop(field_mapping[field])
                    elif field == "categ_ids":
                        vals[field_mapping[field]] = value.mapped("name")
                    elif field == "recurrence_id":
                        if value not in recurrent_rule_ids[operation]:
                            recurrent_rule_ids[operation].append(value)
                            rrule = self.get_rrule_dict(value._rrule_serialize())
                            if rrule.get("UNTIL"):
                                rrule.update({"UNTIL": parse(rrule.get("UNTIL"))})
                            vals[field_mapping[field]] = rrule
                    else:
                        vals[field_mapping[field]] = value
                # Get the Nextcloud calendar
                event_name = vals["summary"]
                nc_calendar_id = (
                    sync_user_id.nc_calendar_id
                    if sync_user_id.nc_calendar_id
                    else False
                )
                if event_id["nc_calendar_ids"]:
                    event_nc_calendar_id = event_id.nc_calendar_ids.filtered(
                        lambda x: x.user_id == event_id.user_id
                    )
                    if event_nc_calendar_id:
                        nc_calendar_id = event_nc_calendar_id

                if event_id.recurrence_id or event_id.nc_rid:
                    event_id, operation, vals = self.manage_recurring_instance(
                        event, operation, vals
                    )
                    if operation == "null":
                        params["create_count"] += len(
                            event_id.recurrence_id.calendar_event_ids.filtered(
                                lambda x: x.nc_to_delete
                            )
                        )
                        operation = current_operation
                        continue
                elif not event_id.recurrence_id and operation != prev_operation:
                    operation = prev_operation

                # Perform create operation
                if operation == "create":
                    # Check if event is recurrent and there are exempted dates
                    try:
                        if nc_calendar_id and connection and principal:
                            calendar_obj = self.get_user_calendar(
                                connection, principal, nc_calendar_id.name
                            )
                            new_caldav_event = calendar_obj.save_event(**vals)
                            caldav_event = new_caldav_event
                            # After creating the event, add attendees and
                            # alarms data
                            event = self.add_nc_alarm_data(
                                caldav_event, vals.get("valarm", [])
                            )
                            if attendees:
                                new_caldav_event.parent.save_with_invites(
                                    caldav_event.icalendar_instance,
                                    attendees=attendees,
                                    schedule_agent="NONE",
                                )
                            vevent = caldav_event.vobject_instance.vevent
                            params["create_count"] += 1
                        else:
                            params["error_count"] += 1
                            raise ValidationError(
                                _(
                                    "No Nextcloud calendar specified "
                                    "for the event %s for user %s"
                                    % (event_id.name, event_id.user_id.name)
                                )
                            )
                    except Exception as e:
                        message = (
                            "Error creating Nextcloud event '%s' for user '%s':\n"
                            % (event_name, user_name)
                        )
                        log_obj.log_event(
                            mode="error",
                            error=e,
                            message=message,
                            operation_type="create",
                        )
                        params["error_count"] += 1

                # Perform write operation
                if operation == "write" and caldav_event:
                    try:
                        # Check if there is a change in nc_calendar in Odoo
                        od_calendar_url = (
                            nc_calendar_id.calendar_url if nc_calendar_id else False
                        )
                        nc_calendar_url = caldav_event.parent.canonical_url
                        if od_calendar_url != nc_calendar_url and nc_calendar_id:
                            # If the nc_calendar was changed in Odoo,
                            # delete the existing event in Nextcloud
                            # old calendar and recreate the same event
                            # in Nextcloud on the new calendar
                            event_data = caldav_event.data
                            new_calendar_obj = self.get_user_calendar(
                                connection, principal, nc_calendar_id.name
                            )
                            caldav_event = new_calendar_obj.add_event(event_data)
                            old_event = caldav_event.event_by_uid(event_id.nc_uid)
                            old_event.delete()
                        # Remove the current event dtstart and dtend values if
                        # its an allday event in Nextcloud but not in Odoo
                        if not event_id.allday and event_id.nc_allday:
                            vevent.contents.pop("dtstart")
                            vevent.contents.pop("dtend")
                        # Update the event alarms (alarm_ids)
                        event = self.add_nc_alarm_data(
                            caldav_event, vals.pop("valarm", [])
                        )
                        # Handle special case when no value exist for some
                        # fields
                        for f in [
                            "transp",
                            "description",
                            "location",
                            "dtstart",
                            "dtend",
                        ]:
                            # if no value exist in Odoo, remove the field in
                            # Nextcloud event
                            if f not in vals and f != "transp":
                                vevent.contents.pop(f, False)
                            # if no value exist in Nextcloud, use the value
                            # from Odoo
                            elif not vevent.contents.get(f, False):
                                caldav_event.icalendar_component.add(f, vals.pop(f))
                        # Update rest of remaining fields
                        [
                            exec(
                                f"caldav_event.vobject_instance.vevent.{i}.value = val",
                                {"caldav_event": caldav_event, "val": vals[i]},
                            )
                            for i in vals
                        ]
                        # Update attendees
                        if "attendee" in vevent.contents:
                            vevent.contents.pop("attendee")
                        if attendees:
                            for attendee in attendees:
                                caldav_event.add_attendee(attendee)
                            # caldav_event.parent.save_with_invites(
                            #     caldav_event.icalendar_instance,
                            #     attendees=attendees,
                            #     schedule_agent="NONE",
                            # )
                        params["write_count"] += 1
                    except Exception as e:
                        message = (
                            "Error updating Nextcloud event '%s' for user '%s':\n"
                            % (event_name, user_name)
                        )
                        log_obj.log_event(
                            mode="error",
                            error=e,
                            message=message,
                            operation_type="write",
                        )
                        params["error_count"] += 1

                # Save changes to the event after create/write operation
                if operation in ("create", "write"):
                    try:
                        caldav_event.save()
                        event_hash = sync_user_id.get_nc_event_hash_by_uid(
                            vevent.uid.value
                        )
                        # Update the Odoo event record
                        res = {"nc_synced": True}
                        if "nc_hash_ids" not in res:
                            res["nc_hash_ids"] = []
                        event_nchash_id = event_id.nc_hash_ids.filtered(
                            lambda x: x.nc_sync_user_id == sync_user_id
                        )
                        res["nc_hash_ids"].append(
                            (
                                0 if not event_nchash_id else 1,
                                0 if not event_nchash_id else event_nchash_id[0].id,
                                {
                                    "nc_sync_user_id": sync_user_id.id,
                                    "nc_event_hash": event_hash,
                                },
                            )
                        )
                        update_events_hash[event_id.nc_uid] = event_id
                        nc_user_ids = params["nc_user_ids"]
                        if nc_user_ids:
                            for nc_user_id in nc_user_ids:
                                nc_user_event_hash = (
                                    nc_user_id.get_nc_event_hash_by_uid(
                                        vevent.uid.value
                                    )
                                )
                                event_nchash_id = event_id.nc_hash_ids.filtered(
                                    lambda x: x.nc_sync_user_id == nc_user_id
                                )
                                res["nc_hash_ids"].append(
                                    (
                                        0 if not event_nchash_id else 1,
                                        0
                                        if not event_nchash_id
                                        else event_nchash_id[0].id,
                                        {
                                            "nc_sync_user_id": nc_user_id.id,
                                            "nc_event_hash": nc_user_event_hash,
                                        },
                                    )
                                )

                        if event_id.recurrence_id:
                            hash_updated = False
                            if (
                                not event_id.nc_detach
                                and event_id.recurrence_id.base_event_id == event_id
                            ):
                                if caldav_event.icalendar_component.get(
                                    "DTSTART"
                                ) and caldav_event.icalendar_component.get("RRULE"):
                                    event_start_date = (
                                        caldav_event.icalendar_component.get(
                                            "DTSTART"
                                        ).dt
                                    )
                                    tz = False
                                    if isinstance(event_start_date, datetime):
                                        tz = event_start_date.tzinfo.zone
                                    if tz:
                                        if event_id.nextcloud_event_timezone != tz:
                                            res["nextcloud_event_timezone"] = tz
                                res["nextcloud_rrule"] = (
                                    vevent.contents.get("rrule", False)
                                    and vevent.rrule.value
                                    or event_id.nextcloud_rrule
                                    or event_id.rrule
                                )
                                event_id.recurrence_id.calendar_event_ids.with_context(
                                    sync_from_nextcloud=True
                                ).write(res)
                                event_id.recurrence_id.calendar_event_ids.filtered(
                                    lambda x: not x.nc_hash_ids
                                ).write(
                                    {
                                        "nc_hash_ids": [
                                            (
                                                0,
                                                0,
                                                {
                                                    "nc_sync_user_id": sync_user_id.id,
                                                    "nc_event_hash": event_hash,
                                                },
                                            )
                                        ]
                                    }
                                )
                                event_id.recurrence_id.calendar_event_ids.filtered(
                                    lambda x: not x.nc_uid
                                ).write({"nc_uid": vevent.uid.value})
                                hash_updated = True
                            if not hash_updated:
                                event_vals = {
                                    "nc_uid": vevent.uid.value,
                                    "nc_hash_ids": res["nc_hash_ids"],
                                }
                            else:
                                event_vals = {}
                            if event_id.nc_detach:
                                if (
                                    event_id.recurrence_id
                                    and event_id.recurrence_id.base_event_id == event_id
                                ):
                                    new_base_event = (
                                        event_id.recurrence_id.calendar_event_ids
                                        - event_id
                                    ).sorted(key=lambda r: r.start)
                                    if new_base_event:
                                        event_id.recurrence_id.base_event_id = (
                                            new_base_event[0].id
                                        )
                                event_vals.update(
                                    {
                                        "recurrence_id": False,
                                        "recurrency": False,
                                        "nc_detach": False,
                                    }
                                )
                            event_id.with_context(sync_from_nextcloud=True).write(
                                event_vals
                            )
                        else:
                            res.update({"nc_uid": vevent.uid.value})
                            if event_id.nc_detach:
                                if (
                                    event_id.recurrence_id
                                    and event_id.recurrence_id.base_event_id == event_id
                                ):
                                    new_base_event = (
                                        event_id.recurrence_id.calendar_event_ids
                                        - event_id
                                    ).sorted(key=lambda r: r.start)
                                    if new_base_event:
                                        event_id.recurrence_id.base_event_id = (
                                            new_base_event[0].id
                                        )
                                res.update(
                                    {
                                        "recurrence_id": False,
                                        "recurrency": False,
                                        "nc_detach": False,
                                    }
                                )
                            event_id.with_context(sync_from_nextcloud=True).write(res)
                        # Commit the changes to the database since it is
                        # already been updated in Nextcloud
                        self.env.cr.commit()
                    except Exception as e:
                        message = "Error saving event '{}' for user '{}':\n".format(
                            event_name,
                            user_name,
                        )
                        log_obj.log_event(
                            mode="error",
                            error=e,
                            message=message,
                            operation_type="write",
                        )

                # Perform delete operation
                if operation == "delete":
                    try:
                        # Delete the event in Nextcloud first before deleting
                        # it in Odoo
                        # Delete all Odoo events with the same nc_uid
                        # TODO: Handle deletion of specific instance of a
                        # recurring event where nc_uid are the same
                        all_events_with_nc_uid = params["all_odoo_event_ids"].filtered(
                            lambda x: x.nc_uid == event_id.nc_uid
                        )
                        to_delete_event_ids = all_events_with_nc_uid.filtered(
                            lambda x: x.nc_to_delete
                        )
                        params["all_odoo_event_ids"] = params[
                            "all_odoo_event_ids"
                        ].filtered(lambda x: x not in to_delete_event_ids)
                        if not (len(all_events_with_nc_uid) - len(to_delete_event_ids)):
                            caldav_event.delete()
                        to_delete_event_ids.sudo().with_context(
                            force_delete=True
                        ).unlink()
                        # Commit the changes to the database since it is
                        # already been deleted in Nextcloud
                        self.env.cr.commit()
                        params["delete_count"] += 1
                    except Exception as e:
                        message = "Error deleting event '{}' for user '{}':\n".format(
                            event_name,
                            user_name,
                        )
                        log_obj.log_event(
                            mode="error",
                            error=e,
                            message=message,
                            operation_type="delete",
                        )
                        params["error_count"] += 1
        return params

    def sync_cron(self):
        """
        This method triggers the sync event operation
        """
        self = self.sudo()
        per_user_id = self._context.get("per_user", False)
        # Start Sync Process: Date + Time
        sync_start = datetime.now()
        result = self.env["nc.sync.log"].log_event("pre_sync")
        log_obj = result["log_id"]
        calendar_event_obj = self.env["calendar.event"]
        # To minimize impact on performance, search only once rather than
        # searching each loop
        params = {
            "log_obj": result["log_id"],
            "all_nc_calendar_ids": self.env["nc.calendar"].search(
                [("user_id", "!=", False)]
            ),
            "all_user_ids": self.env["res.users"].search([]),
            "all_sync_user_ids": self.env["nc.sync.user"].search(
                [("sync_calendar", "=", True)]
            ),
            "all_partner_ids": self.env["res.partner"].search([("email", "!=", False)]),
            "all_odoo_event_type_ids": self.env["calendar.event.type"].search([]),
            "status_vals": {
                "confirmed": self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_confirmed"
                ).id,
                "tentative": self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_tentative"
                ).id,
                "cancelled": self.env.ref(
                    "nextcloud_odoo_sync.nc_event_status_canceled"
                ).id,
            },
            "create_count": 0,
            "write_count": 0,
            "delete_count": 0,
            "error_count": 0,
        }
        if not per_user_id:
            params["all_odoo_event_ids"] = calendar_event_obj.search([])
        if result["log_id"] and result["resume"]:
            sync_users_domain = [("sync_calendar", "=", True)]
            if per_user_id:
                sync_users_domain.append(("user_id", "=", per_user_id.id))
            sync_users = self.env["nc.sync.user"].search(sync_users_domain)
            for user in sync_users:
                # Get all events from Odoo and Nextcloud
                # log_obj.log_event(message="Getting events for '%s'" % user.user_id.name)
                if per_user_id:
                    start_date = datetime.combine(
                        user.start_date or dtdate.today(), datetime.min.time()
                    )
                    params["all_odoo_event_ids"] = calendar_event_obj.search(
                        [("start", ">=", start_date)], order="start"
                    )
                events_dict = user.get_all_user_events(**params)
                od_events = events_dict["od_events"]
                nc_events = events_dict["nc_events"]
                connection = events_dict["connection"]
                principal = events_dict["principal"]
                if connection and principal:
                    params.update({"connection": connection, "principal": principal})
                    # # Compare all events
                    # log_obj.log_event(
                    #     message="Comparing events for '%s'" % user["user_name"]
                    # )
                    od_events_dict, nc_events_dict = self.compare_events(
                        od_events, nc_events, user, log_obj
                    )
                    # # Log number of operations to do
                    # all_stg_events = {
                    #     "Nextcloud": nc_events_dict,
                    #     "Odoo": od_events_dict,
                    # }
                    # for stg_events in all_stg_events:
                    #     message = "%s:" % stg_events
                    #     for operation in all_stg_events[stg_events]:
                    #         count = len(all_stg_events[stg_events][operation])
                    #         message += " {} events to {},".format(count, operation)
                    #     log_obj.log_event(message=message.strip(","))
                    # Update events in Odoo and Nextcloud
                    # log_obj.log_event(message="Updating Odoo events")
                    params = self.update_odoo_events(user, od_events_dict, **params)
                    # log_obj.log_event(message="Updating Nextcloud events")
                    params = self.update_nextcloud_events(
                        user, nc_events_dict, **params
                    )
            # Compute duration of sync operation
            log_obj.duration = log_obj.get_time_diff(sync_start)
            summary_message = """- Total create {}
- Total write {}
- Total delete {}
- Total error {}""".format(
                params["create_count"],
                params["write_count"],
                params["delete_count"],
                params["error_count"],
            )
            log_obj.log_event(message="""End Sync Process\n%s""" % summary_message)
            log_obj.write({"description": summary_message, "date_end": datetime.now()})

    def add_nc_alarm_data(self, event, valarm):
        """
        This method adds reminders on a nextcloud event
        :param event: Caldav Nextcloud event
        :param valarm: list of event reminders/alarms
                operations for Nextcloud
        :return event: returns a Caldav Nextcloud event with the
                    corresponding reminders
        """
        if valarm:
            event.vobject_instance.vevent.contents.pop("valarm", False)
            for item in valarm:
                alarm_obj = Alarm()
                alarm_obj.add("action", "DISPLAY")
                alarm_obj.add("TRIGGER;RELATED=START", item)
                event.icalendar_component.add_component(alarm_obj)
        return event

    def get_user_calendar(self, connection, connection_principal, nc_calendar):
        """
        This record gets the Caldav record on the event besed on the name.
        It will create a new calendar record in nextcloud if it does not exist
        :param connection: Caldav user connection data
        :param connection_principal: Caldav user connection principal data
        :param nc_calendar: Calendar name (String)
        :return calendar_obj: Caldav calendar object
        """
        try:
            principal_calendar_obj = connection_principal.calendar(name=nc_calendar)
            principal_calendar_obj.events()
            calendar_obj = connection.calendar(url=principal_calendar_obj.url)
        except BaseException:
            calendar_obj = connection_principal.make_calendar(name=nc_calendar)
        return calendar_obj

    def check_nextcloud_connection(self, url, username, password):
        """
        This method checks the NextCloud connection
        :param url: string, NextCloud server URL
        :param username: string, NextCloud username
        :param password: string, NextCloud password
        @return tuple: Caldav client object, client principal / dictionary
        """
        with caldav.DAVClient(url=url, username=username, password=password) as client:
            try:
                return client, client.principal()
            except caldav.lib.error.NotFoundError as e:
                _logger.warning("Error: %s" % e)
                return client, {
                    "sync_error_id": self.sudo().env.ref(
                        "nextcloud_odoo_sync.nc_sync_error_1001"
                    ),
                    "response_description": str(e),
                }
            except caldav.lib.error.AuthorizationError as e:
                _logger.warning("Error: %s" % e)
                return client, {
                    "sync_error_id": self.sudo().env.ref(
                        "nextcloud_odoo_sync.nc_sync_error_1000"
                    ),
                    "response_description": str(e),
                }
            except (
                caldav.lib.error.PropfindError,
                requests.exceptions.ConnectionError,
            ) as e:
                _logger.warning("Error: %s" % e)
                return client, {
                    "sync_error_id": self.sudo().env.ref(
                        "nextcloud_odoo_sync.nc_sync_error_1001"
                    ),
                    "response_description": str(e),
                }

    def get_alarms_mapping(self):
        """
        This method returns the equivalent record ID of Odoo calendar.alarm model
        based according to Nextcloud alarm code
        :return dictionary
        {string: Nextcloud alarm code, integer: Odoo calendar.alarm record id}
        """
        alarm_mapping = {
            "PT0S": "nextcloud_odoo_sync.calendar_alarm_notif_at_event_start",
            "-PT5M": "nextcloud_odoo_sync.calendar_alarm_notif_5_mins",
            "-PT10M": "nextcloud_odoo_sync.calendar_alarm_notif_10_mins",
            "-PT15M": "calendar.alarm_notif_1",
            "-PT30M": "calendar.alarm_notif_2",
            "-PT1H": "calendar.alarm_notif_3",
            "-PT2H": "calendar.alarm_notif_4",
            "-P1D": "calendar.alarm_notif_5",
            "-P2D": "nextcloud_odoo_sync.calendar_alarm_notif_2_days",
        }
        result = {}
        for alarm_code in alarm_mapping:
            try:
                result.update({alarm_code: self.env.ref(alarm_mapping[alarm_code]).id})
            except Exception:
                result.update({alarm_code: False})
        return result

    def get_odoo_alarms(self, valarm):
        """
        This method is used to get the Nextcloud alarm code and
        find the equivalent record ID in Odoo calendar.alarm model
        :param valarm: dictionary of Nextcloud alarms from the event
        :return list: List of values to populate a many2many field
        """
        result = []
        alarms_mapping = self.get_alarms_mapping()
        for v_item in valarm:
            if isinstance(v_item, dict):
                v_item.pop("ACTION", False)
                val = [v_item[x] for x in v_item]
                if val:
                    alarm_id = alarms_mapping.get(val[0])
                    if alarm_id:
                        result.append(alarm_id)
        return [(6, 0, result)]

    def get_odoo_categories(self, categ_ids, value):
        """
        This method returns the corresponding odoo data result
        for categ_ids field
        :param categ_ids: categories record set
        :param value: comma separated string of categories
        :return odoo value for categ_ids and updated value for categ_ids
        """
        result = []
        if value:
            for category in value.lower().split(","):
                category_id = categ_ids.filtered(lambda x: x.name.lower() == category)
                if not category_id:
                    category_id = categ_ids.create({"name": category})
                    categ_ids |= category_id
                result.append(category_id.id)
        return [(6, 0, result)], categ_ids

    def get_caldav_fields(self):
        """
        Function for mapping of CalDav fields to Odoo fields
        :return dictionary: CalDav fields as key and Odoo
                calendar.event model fields as value
        """
        return {
            "summary": "name",
            "dtstart": "start",
            "dtend": "stop",
            "description": "description",
            "status": "nc_status_id",
            "location": "location",
            "attendee": "partner_ids",
            "categories": "categ_ids",
            "transp": "show_as",
            "uid": "nc_uid",
            "valarm": "alarm_ids",
            "rrule": "recurrence_id",
            "recurrence-id": "nc_rid",
            "last-modified": "write_date",
            "id": "id",
        }

    def convert_date(self, dt, tz, mode):
        """
        This method converts datetime object to UTC and vice versa
        :param dt, datetime object
        :param tz, string (e.g. "Asia/Manila")
        :param mode, string ("utc":local time -> utc,
            "local":utc -> local time)
        :return: datetime
        """
        dt_conv = False
        if mode and dt and tz:
            if mode == "utc":
                dt_tz = pytz.timezone(tz).localize(dt, is_dst=None)
                dt_conv = dt_tz.astimezone(pytz.utc).replace(tzinfo=None)
            if mode == "local":
                dt_tz = dt.replace(tzinfo=pytz.utc)
                dt_conv = dt_tz.astimezone(pytz.timezone(tz))
        return dt_conv

    def update_recurring_events_in_all_events(
        self, new_recurring_events, recurring_events, all_odoo_event_ids
    ):
        for event in recurring_events:
            if not event.exists():
                all_odoo_event_ids = all_odoo_event_ids - event
        for event in new_recurring_events:
            if event not in all_odoo_event_ids:
                all_odoo_event_ids = all_odoo_event_ids + event
        return all_odoo_event_ids

    def check_recurrent_event_vals(self, od_event_id, vals):
        update = False
        if (
            vals.get("nextcloud_rrule", "") != od_event_id.nextcloud_rrule
            or vals.get("name", "") != od_event_id.name
            or vals.get("show_as", "") != od_event_id.show_as
        ):
            update = True
        elif (
            vals.get("description", False)
            and vals.get("description") != od_event_id.description
        ) or (
            vals.get("location", False) and vals.get("location") != od_event_id.location
        ):
            update = True
        if od_event_id.allday:
            if (
                vals.get("start_date", False)
                and vals.get("start_date") != od_event_id.start_date
            ) or (
                vals.get("stop_date", False)
                and vals.get("stop_date") != od_event_id.stop_date
            ):
                update = True
        else:
            if (
                vals.get("start", False) and vals.get("start") != od_event_id.start
            ) or (vals.get("stop", False) and vals.get("stop") != od_event_id.stop):
                update = True
        if vals.get("alarm_ids", []):
            new_vals = vals.get("alarm_ids")[0][2]
            alarm_ids = od_event_id.alarm_ids.ids
            if len(alarm_ids) != len(new_vals):
                update = True
            for rec in new_vals:
                if rec not in alarm_ids:
                    update = True
                    break
        if vals.get("categ_ids", []):
            new_vals = vals.get("categ_ids")[0][2]
            categ_ids = od_event_id.categ_ids.ids
            if len(categ_ids) != len(new_vals):
                update = True
            for rec in new_vals:
                if rec not in categ_ids:
                    update = True
                    break
        if vals.get("partner_ids", []):
            new_vals = vals.get("partner_ids")[0][2]
            partner_ids = od_event_id.partner_ids.ids
            if len(partner_ids) != len(new_vals):
                update = True
            for rec in new_vals:
                if rec not in partner_ids:
                    update = True
                    break
        return update
