from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["membership.group"].search([]).write(
        {
            "website_snippet_wrap_classes": "mg_wrap mg_show_image mg_show_team",
            "website_snippet_members_classes": "mg_layout_grid mg_show_team_desc",
        }
    )
