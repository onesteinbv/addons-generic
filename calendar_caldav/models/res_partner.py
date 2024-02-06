import re

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def import_caldav_address(self, address):
        match = re.search("^(mailto|MAILTO):(.*)$", address)
        if not match:
            raise Exception("Failed to find an email address (%s)" % address)
        email = match.group(2)
        partner = self.search([("email", "=ilike", email)], limit=1)
        if not partner:
            partner = self.create(
                {  # Move to prepare method?
                    "name": address.params.get("CN", email),
                    "email": email,
                    "company_type": "person",  # Check CUTYPE?
                }
            )
        return partner
