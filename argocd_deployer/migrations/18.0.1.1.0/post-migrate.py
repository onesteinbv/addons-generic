from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Set the application set configs to the current live config for all existing application sets."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    app_set_model = env["argocd.application.set"]
    app_sets = app_set_model.search([])
    for app_set in app_sets:
        app_set.config = app_set.config_live
