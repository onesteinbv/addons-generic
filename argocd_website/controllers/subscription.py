from odoo.osv import expression

from odoo.addons.subscription_portal.controllers.main import PortalSubscription


class ArgoCDPortalSubscription(PortalSubscription):
    def _get_filter_domain(self, kw):
        res = super()._get_filter_domain(kw)
        res = expression.AND(
            [
                res,
                [
                    "|",
                    ("website_id", "=", False),
                    "&",
                    ("stage_id.type", "!=", "draft"),
                    ("stage_id", "!=", False),
                ],
            ]
        )
        return res
