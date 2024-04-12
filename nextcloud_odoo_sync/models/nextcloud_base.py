# Copyright (c) 2022 iScale Solutions Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import requests
from odoo import models
from odoo.http import request


class NextcloudBase(models.AbstractModel):
    _name = "nextcloud.base"
    _description = "NextCloud Base API"

    """
    These functions were derived from:
    https://github.com/EnterpriseyIntranet/nextcloud-API
    """

    # def get_auth_data(self):
    #     """
    #     Get and return nextcloud authentication data
    #     :return Dictionary: nextcloud authentication data
    #     """
    #     config_obj = self.env["ir.config_parameter"]
    #     data = {
    #         "h_get": {"OCS-APIRequest": "true"},
    #         "h_post": {
    #             "OCS-APIRequest": "true",
    #             "Content-Type": "application/x-www-form-urlencoded",
    #         },
    #         "auth_pk": (
    #             config_obj.sudo().get_param("nextcloud_odoo_sync.nextcloud_login"),
    #             config_obj.sudo().get_param("nextcloud_odoo_sync.nextcloud_password"),
    #         ),
    #     }
    #     return data
    #
    # def get_full_url(self, additional_url="", api_url=""):
    #     """
    #     Build full url for request to NextCloud api
    #     Construct url from self.base_url, self.API_URL,
    #         additional_url (if given),
    #     add format=json param if self.json
    #     :param additional_url: str
    #         add to url after api_url
    #     :return: str
    #     """
    #     if additional_url and not str(additional_url).startswith("/"):
    #         additional_url = "/{}".format(additional_url)
    #     config_obj = self.env["ir.config_parameter"]
    #     res = "{base_url}{api_url}{additional_url}".format(
    #         base_url=config_obj.sudo().get_param("nextcloud_odoo_sync.nextcloud_url"),
    #         api_url=api_url,
    #         additional_url=additional_url,
    #     )
    #     res += "?format=json"
    #     return res
    #
    def rtn(self, resp):
        """
        converts response a json format
        :param resp: api response
        :return json api response
        """
        return resp.json()
    #
    # def get(self, url="", params=None):
    #     url = self.get_full_url(url, "/ocs/v1.php/cloud/users")
    #     data = self.get_auth_data()
    #     res = requests.get(
    #         url, auth=data["auth_pk"], headers=data["h_get"], params=params
    #     )
    #     return self.rtn(res)
    #
    # def get_users(self, search=None, limit=None, offset=None):
    #     """
    #     Retrieve a list of users from the Nextcloud server
    #     :param search: string, optional search string
    #     :param limit: int, optional limit value
    #     :param offset: int, optional offset value
    #     :return: List of users info
    #     """
    #     params = {"search": search, "limit": limit, "offset": offset}
    #     result = self.get(params=params)
    #     if isinstance(result, dict):
    #         users = []
    #         for uid in result["ocs"]["data"]["users"]:
    #             res = self.get(uid)
    #             users.append(res["ocs"]["data"])
    #         result["ocs"]["data"]["users"] = users
    #     return result

    def get_user(self, uid, url, username, password):
        """
        Retrieve information about a single user
        :param uid: str, uid of user
        :return: Dictionary of user info
        """
        res = "{base_url}{api_url}{additional_url}".format(
            base_url=url,
            api_url="/ocs/v1.php/cloud/users/",
            additional_url=uid,
        )
        res += "?format=json"
        data = {
            "h_get": {"OCS-APIRequest": "true"},
            "h_post": {
                "OCS-APIRequest": "true",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            "auth_pk": (
                username,
                password
            ),
        }
        request = requests.get(
            res, auth=data["auth_pk"], headers=data["h_get"]
        )
        result = self.rtn(request)
        return result["ocs"]["data"]
