from datetime import datetime, timedelta

from odoo import models
from odoo.tools import populate


class MembershipActivity(models.Model):
    _inherit = "membership.activity"
    _populate_dependencies = ["res.partner", "project.project"]
    _populate_sizes = {
        "small": 1000,
        "medium": 50000,
        "large": 100000,
    }

    def _populate_factories(self):
        partner_ids = self.env.registry.populated_models["res.partner"]
        project_ids = self.env.registry.populated_models["project.project"]
        base_date = datetime.now()

        def get_partner_id(random, **kwargs):
            return random.choice(partner_ids)

        def get_project_id(random, **kwargs):
            return random.choice(project_ids)

        return [
            ("partner_id", populate.compute(get_partner_id)),
            ("project_id", populate.compute(get_project_id)),
            (
                "date",
                populate.randdatetime(
                    base_date=base_date, relative_before=timedelta(days=-(3 * 365))
                ),
            ),
        ]
