# © 2023 Onestein
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import ast

from odoo import SUPERUSER_ID, api

ACTIONS = ("calendar.action_calendar_event",)


def uninstall_hook(cr, registry):
    """Restore calendar action"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for action_id in ACTIONS:
        action = env.ref(action_id)
        dom = ast.literal_eval(action.domain or "{}")
        dom = [x for x in dom if x[0] != "nc_to_delete"]
        dom = list(set(dom))
        action.write({"domain": dom})
