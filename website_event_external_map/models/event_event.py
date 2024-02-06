from odoo import models


class EventEvent(models.Model):
    _inherit = "event.event"

    def map_link(self, zoom=8):
        return self._map_link(zoom=zoom)

    def _map_link(self, zoom=8):
        self.ensure_one()
        if self.address_id:
            res = self.address_id.open_map()["url"]
            return res
