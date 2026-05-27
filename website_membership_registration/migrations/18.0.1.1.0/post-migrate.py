from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Enable registration for all published membership groups."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    membership_groups = env["membership.group"].search([("is_published", "=", True)])
    membership_groups.write({"allow_registration": True})
