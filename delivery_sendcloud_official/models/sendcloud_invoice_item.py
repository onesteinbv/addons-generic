# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from odoo import fields, models


class SendcloudInvoice(models.Model):
    _name = "sendcloud.invoice.item"
    _description = "Sendcloud Invoice Items"

    name = fields.Char()
    sendcloud_code = fields.Integer(required=True)
    sendcloud_invoice_id = fields.Many2one("sendcloud.invoice", ondelete="cascade")
