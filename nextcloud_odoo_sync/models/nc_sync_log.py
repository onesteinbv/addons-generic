# Copyright (c) 2023 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import datetime, timedelta
from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)


class NcSyncLog(models.Model):
    _name = "nc.sync.log"
    _description = "Nextcloud Sync Log"
    _order = "create_date desc"

    name = fields.Char(string="Sync code")
    description = fields.Char()
    date_start = fields.Datetime(string="Start")
    date_end = fields.Datetime(string="End")
    state = fields.Selection(
        [
            ("connecting", "Connecting"),
            ("in_progress", "In Progress"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("error", "Error"),
        ],
        string="State",
        default="in_progress",
    )
    next_cloud_url = fields.Char(string="NextCloud URL")
    odoo_url = fields.Char(string="Odoo URL")
    duration = fields.Char()
    line_ids = fields.One2many("nc.sync.log.line", "log_id")

    def get_time_diff(self, date_from, date_to=False):
        """
        This method checks the time difference between two datetime objects
        in hours, minutes and seconds
        @param: date_from, datetime
        @param: date_to, datetime
        @return: string
        """
        if not date_to:
            date_to = datetime.now()
        diff = date_to - date_from
        # Convert the difference to hours, minutes and seconds
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        result = ""
        if hours:
            result += f"{hours} hours "
        if minutes:
            result += f"{minutes} minutes "
        result += f"{seconds} seconds"
        return result

    def check_and_log_users(self, sync_log_id):
        """
        Function to Check and log NextCloud users information.
        :param sync_log_id: single recordset of nc.sync.log model
        :return: List, NextCloud users that are in linked in Odoo
        """
        nc_sync_user_obj = self.env["nc.sync.user"]
        nc_users = self.env["nextcloud.base"].get_users()["ocs"]["data"]["users"]
        nc_user_email = [nc["id"] for nc in nc_users] + [nc["email"] for nc in nc_users]
        odoo_users = nc_sync_user_obj.search_read([("sync_calendar", "=", True)])
        stg_users_odoo_not_in_nc = [
            x for x in odoo_users if x["user_name"] not in nc_user_email
        ]
        stg_users_nc_not_in_odoo = []
        username_list = [o["user_name"].lower() for o in odoo_users]
        for x in nc_users:
            if x["email"] and x["email"].lower() not in username_list:
                if x["displayname"] and x["displayname"].lower() not in username_list:
                    stg_users_nc_not_in_odoo.append(x)
            else:
                stg_users_nc_not_in_odoo.append(x)
        stg_users_nc_in_odoo = []
        # Compare Odoo users with Nextcloud users
        if stg_users_odoo_not_in_nc:
            odoo_usernames = ", ".join(
                [x["name"] for x in stg_users_odoo_not_in_nc if x["name"]]
            )
            sync_log_id.line_ids.create(
                {
                    "log_id": sync_log_id.id,
                    "operation_type": "read",
                    "severity": "info",
                    "response_description": "Compare Odoo users with Nextcloud "
                    "users\n\t\tOdoo users not in Nextcloud: %s" % odoo_usernames,
                }
            )
        # Compare Nextcloud users with Odoo users
        if stg_users_nc_not_in_odoo:
            nc_usernames = ", ".join(
                [x["displayname"] for x in stg_users_nc_not_in_odoo if x["displayname"]]
            )
            sync_log_id.line_ids.create(
                {
                    "log_id": sync_log_id.id,
                    "operation_type": "read",
                    "severity": "info",
                    "response_description": "Compare Nextcloud users with Odoo "
                    "users\n\tNextcloud users not in Odoo: %s" % nc_usernames,
                }
            )
        for odoo_user in odoo_users:
            for nc_user in nc_users:
                user_list = []
                if "email" in nc_user and nc_user["email"]:
                    user_list.append(nc_user["email"].lower())
                if "id" in nc_user and nc_user["id"]:
                    user_list.append(nc_user["id"].lower())
                if odoo_user["user_name"].lower() in user_list:
                    stg_users_nc_in_odoo.append(odoo_user)
                    nc_sync_user_obj.browse(odoo_user["id"]).write(
                        {"nextcloud_user_id": nc_user["id"]}
                    )

        # Number of  users to sync
        count = len(stg_users_nc_in_odoo)
        sync_log_id.line_ids.create(
            {
                "log_id": sync_log_id.id,
                "operation_type": "read",
                "severity": "info",
                "response_description": "Number of users to sync: %s" % count,
            }
        )
        return stg_users_nc_in_odoo

    def log_event(self, mode="text", log_id=False, **params):
        """
        This method takes care of the logging process
        @param: mode, string, indicates the sync phase
        @param: log_id, single recordset of nc.sync.log model
        @return dictionary of values
        """
        result = {"resume": True, "stg_users_nc_in_odoo": []}
        log_line = self.env["nc.sync.log.line"]
        res = {}
        if mode == "pre_sync":
            # Start Sync Process: Date + Time
            datetime_now = datetime.now()
            log_id = self.create(
                {
                    "name": datetime_now.strftime("%Y%m%d-%H%M%S"),
                    "date_start": datetime_now,
                    "state": "connecting",
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "operation_type": "login",
                                "response_description": "Start Sync Process",
                            },
                        )
                    ],
                }
            )
            result["log_id"] = log_id
            # # Nextcloud connection test for Caldav
            # if caldav_sync:
            #     data_send = "url: {}, username: {}, password: ****".format(
            #         nc_url, username
            #     )
            #     res = {
            #         "operation_type": "login",
            #         "log_id": log_id.id,
            #         "data_send": data_send,
            #     }
            #     connection, principal = caldav_obj.check_nextcloud_connection(
            #         url=nc_url, username=username, password=password
            #     )
            #     if not isinstance(principal, dict):
            #         res[
            #             "response_description"
            #         ] = "Nextcloud connection test for Caldav: OK"
            #     else:
            #         response_description = (
            #             """Nextcloud connection test for Caldav: Error
            #             \t%s"""
            #             % principal["response_description"]
            #         )
            #         res.update(
            #             {
            #                 "response_description": response_description,
            #                 "error_code_id": principal["sync_error_id"].id
            #                 if "sync_error_id" in principal
            #                 else False,
            #             }
            #         )
            #         result["resume"] = False
            #     log_line.create(res)
            #
            # # Compare Nextcloud users with Odoo users and vice versa
            # if result["resume"] and log_id:
            #     result["stg_users_nc_in_odoo"] = self.check_and_log_users(log_id)
        else:
            error = str(params["error"]) if "error" in params else False
            severity = params["severity"] if "severity" in params else "info"
            operation_type = (
                params["operation_type"] if "operation_type" in params else "read"
            )
            if not log_id:
                log_id = self.browse(self.ids[0])
            res = {
                "log_id": log_id.id,
                "operation_type": operation_type,
                "severity": severity,
            }

            if mode == "text" and "message" in params:
                res["response_description"] = params["message"]

            elif mode == "error" and error:
                # Undo the last uncommitted changes
                self.env.cr.rollback()
                message = "%s " % params["message"] if "message" in params else ""
                res["response_description"] = """{}{}""".format(message, error)

            try:
                log_line.create(res)
            except Exception as e:
                _logger.warning("Error encountered during log operation: %s" % e)
                return result

        # Create an event log
        if "response_description" in res:
            _logger.warning(res["response_description"])
        # Commit the changes to the database
        self.env.cr.commit()
        return result

    def delete_logs(self):
        config = self.env["ir.config_parameter"].sudo()
        capacity_value = (
            7
            if not config.get_param("nextcloud_odoo_sync.log_capacity")
            else config.get_param("nextcloud_odoo_sync.log_capacity")
        )
        date_capacity = datetime.now() - timedelta(days=int(capacity_value))
        date_capacity = date_capacity.strftime("%Y-%m-%d %H:%M:%S")
        sync_log_ids = self.search(
            [("create_date", "<", date_capacity)], order="create_date desc"
        )
        sync_log_ids.unlink()


class NcSyncLogLine(models.Model):
    _name = "nc.sync.log.line"
    _description = "Nextcloud Sync Log Line"

    log_id = fields.Many2one("nc.sync.log", "Log ID", ondelete="cascade")
    operation_type = fields.Selection(
        [
            ("create", "Create"),
            ("write", "Write"),
            ("delete", "Delete"),
            ("read", "Read"),
            ("login", "Login"),
            ("conflict", "Conflict"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        string="Operation Type",
    )
    data_send = fields.Text("Data Sent")
    error_code_id = fields.Many2one("nc.sync.error", "Error Code")
    severity = fields.Selection(
        [
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ],
        string="Severity",
        default="info",
    )
    response_description = fields.Text("Response Description")
