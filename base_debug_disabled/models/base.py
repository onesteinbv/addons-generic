# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def user_has_groups(self, groups):
        """Return False for users in the Disallow Debug Mode group."""
        group_no_one = "base.group_no_one"
        if (
            self.env.user != self.env.ref("base.user_admin")
            and group_no_one in groups.split(",")
            and self.user_has_groups("base_debug_disabled.group_disallow_debug_mode")
        ):
            return False
        return super().user_has_groups(groups)
