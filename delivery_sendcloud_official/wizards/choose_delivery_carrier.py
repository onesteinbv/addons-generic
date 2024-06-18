# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from odoo import api, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        res = super()._onchange_carrier_id()
        if self.delivery_type == "sendcloud":
            vals = self._get_shipment_rate()
            if vals.get("error_message"):
                return {"error": vals["error_message"]}
        return res

    def button_confirm(self):
        vals = self.carrier_id.rate_shipment(self.order_id)
        if vals.get("sendcloud_country_specific_product"):
            self = self.with_context(
                sendcloud_country_specific_product=vals[
                    "sendcloud_country_specific_product"
                ]
            )
        return super(ChooseDeliveryCarrier, self).button_confirm()
