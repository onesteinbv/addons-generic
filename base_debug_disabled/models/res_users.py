# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    # For a user which is not erp manager, the disallow debug mode group won't
    # even appear on the user form view. This implies that the default (taken
    # from default user) won't be passed to the create method. We take care of
    # this issue here
    @api.model_create_multi
    def create(self, vals_list):
        is_erp_manager = self.user_has_groups("base.group_erp_manager")
        if not is_erp_manager:
            disallow_debug_mode_group = self.env.ref(
                "base_debug_disabled.group_disallow_debug_mode"
            )
            disallow_debug_mode_group_str = "in_group_" + str(
                disallow_debug_mode_group.id
            )
            for vals in vals_list:
                if disallow_debug_mode_group_str not in vals:
                    vals[disallow_debug_mode_group_str] = True
        return super().create(vals_list)
