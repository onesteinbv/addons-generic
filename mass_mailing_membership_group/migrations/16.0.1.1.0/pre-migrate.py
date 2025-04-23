from odoo import api, SUPERUSER_ID


def migrate(cr, installed_version):
    # Remove old view from database
    env = api.Environment(cr, SUPERUSER_ID, {})
    view = env.ref("mass_mailing_membership_group.view_partner_form", raise_if_not_found=False)
    if view:
        view.unlink()
