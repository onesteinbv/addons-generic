# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from odoo import models


class SendcloudCancelShipmentConfirmWizard(models.TransientModel):
    _name = "sendcloud.cancel.shipment.confirm.wizard"
    _description = "Sendcloud Cancel Shipment Confirm Wizard"

    def do_cancel_shipment(self):
        active_id = self.env.context.get("active_id")
        if active_id and self.env.context.get("active_model") == "stock.picking":
            ctx = self.env.context.copy()
            ctx["do_sendcloud_cancel_shipment"] = True
            ctx["skip_sync_picking_to_sendcloud"] = True
            picking = self.env["stock.picking"].browse(active_id)
            picking.with_context(ctx).cancel_shipment()
