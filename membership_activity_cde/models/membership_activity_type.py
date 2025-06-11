from odoo import _, models
from odoo.exceptions import UserError


class MembershipActivityType(models.Model):
    _inherit = "membership.activity.type"

    def unlink(self):
        protected_types = self.env["membership.activity.type"]
        protected_types += self.env.ref("membership_activity_cde.pr")
        protected_types += self.env.ref("membership_activity_cde.commit")
        protected_types += self.env.ref("membership_activity_cde.issue")
        protected_types += self.env.ref("membership_activity_cde.review")
        protected_types += self.env.ref("membership_activity_cde.comment")
        protected_types_ids = set(protected_types.ids)
        ids = set(self.ids)
        if ids.intersection(protected_types_ids):
            raise UserError(_("These activity types cannot be deleted."))
        return super().unlink()
