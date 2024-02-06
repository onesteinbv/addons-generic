# Copyright 2017-2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def _visible_menu_ids(self, debug=False):
        """Set debug = False, if the user is in the group Disallow Debug Mode."""
        if self.user_has_groups("base_debug_disabled.group_disallow_debug_mode"):
            debug = False
        return super()._visible_menu_ids(debug=debug)
