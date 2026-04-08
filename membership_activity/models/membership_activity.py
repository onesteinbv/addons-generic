from odoo import api, fields, models


class MembershipActivity(models.Model):
    _name = "membership.activity"
    _description = "Member Activity"

    def init(self):
        super().init()
        # Create an index to speed up searching for duplicate activities
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS membership_activity_url_project_type_index
            ON membership_activity (url, project_id, type_id)
            """
        )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Member",
        ondelete="cascade",
        store=True,
        compute="_compute_partner_id",
    )
    project_id = fields.Many2one(
        comodel_name="project.project", string="Related Project", ondelete="cascade"
    )
    date = fields.Datetime(required=True, index=True)
    url = fields.Char(
        index=True
    )
    type_id = fields.Many2one(
        comodel_name="membership.activity.type", string="Activity Type", 
        index=True
    )

    @api.depends("partner_id", "partner_id.display_name")
    def _compute_display_name(self):
        for activity in self:
            activity.display_name = activity.partner_id.display_name

    def _compute_partner_id(self):
        # To be implemented by other modules
        # For example for CDE activity, the activity can be created before the member
        # is created in the system
        pass

    def reconcile_partner(self):
        self._compute_partner_id()
