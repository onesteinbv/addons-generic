from . import models
from . import wizard
from odoo import SUPERUSER_ID, api

def _mail_post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['mail.alias.domain']._migrate_icp_to_domain()
